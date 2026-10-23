"""Auto-resume restart-loop breaker (defense-3).

Defenses 1-2 (``_HERMES_GATEWAY`` guard on ``hermes gateway stop|restart`` /
``terminal_tool``, cron lifecycle filter) stop the agent scheduling its own restart
but not every SIGTERM source: the supervisor respawns, the gateway auto-resumes the
restart-interrupted session, whose next turn re-runs the offending logic.  Boots are
persisted to ``<HERMES_HOME>/gateway/restart_loop.json`` and CHAIN while gaps stay
within ``max_gap_seconds`` (a ~150s watchdog-kill cycle trips like a ~10s loop).
Tripped → caller SKIPS auto-resume.  Any I/O failure fails OPEN, never wedging.
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
from typing import List, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger("gateway.run")

# A legitimate operator restart (or two) never trips; a ~10s respawn loop does
# within a few cycles.
DEFAULT_MAX_RESTARTS = 3
DEFAULT_WINDOW_SECONDS = 60
# Longest gap between consecutive restart-interrupted boots still counted as the
# SAME loop.  A fixed-window prune only sees cycles faster than the window (a slower
# loop drops its history every boot and never trips); chaining on the inter-boot
# gap is period-agnostic, and real quiet resets it.
DEFAULT_MAX_GAP_SECONDS = 300
# Below this system uptime a boot is treated as part of a genuine HOST reboot (kernel/VPS
# restart, e.g. a runtime upgrade that reboots the box) rather than a self-inflicted respawn
# loop. During a real reboot several supervised slots can race for the host lock for a couple
# of minutes and produce a fast, LEGITIMATE restart-interrupted cascade; counting those as a
# loop disables auto-resume until manual intervention. Boots this soon after the host came up
# do NOT extend the loop chain and RESET it. A crash-loop inside a long-lived host has high
# uptime and is still capped hard. <=0 disables the grace entirely.
DEFAULT_REBOOT_GRACE_SECONDS = 120
# Only the newest ``max_restarts`` entries can change a verdict; the rest are forensics.
_MAX_STORED_BOOTS = 50


def _state_path():
    return get_hermes_home() / "gateway" / "restart_loop.json"


def _system_uptime_seconds() -> Optional[float]:
    """Seconds since the host booted, from ``/proc/uptime``; ``None`` when unreadable.

    Fails CLOSED for the grace feature: an unknown uptime means we CANNOT prove a real host
    reboot, so callers must keep counting the boot normally (the breaker stays fully armed).
    """
    try:
        with open("/proc/uptime", encoding="utf-8") as fh:
            return float(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _is_host_reboot_boot(reboot_grace_seconds: int, *, uptime: Optional[float] = None) -> bool:
    """True when this boot happened within ``reboot_grace_seconds`` of the host coming up.

    Such a boot is part of a genuine host-reboot cascade, not a self-inflicted respawn loop,
    so it must not extend or trip the loop chain. Requires a KNOWN low uptime: if uptime is
    unreadable or the grace is disabled (<=0), returns False so the breaker stays armed.
    """
    if reboot_grace_seconds <= 0:
        return False
    up = _system_uptime_seconds() if uptime is None else uptime
    return up is not None and up < reboot_grace_seconds


def _load_boots() -> list[float]:
    try:
        # utf-8-sig: our BOM-tolerant read fix for the persisted boot log.
        raw = _state_path().read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        boots = data.get("boots", [])
        return [float(t) for t in boots if isinstance(t, (int, float))]
    except (OSError, ValueError, TypeError):
        return []


def _save_boots(boots: list[float]) -> None:
    with contextlib.suppress(OSError):
        path = _state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"boots": boots}), encoding="utf-8")


def _chain_gap(window_seconds: int, max_gap_seconds: int) -> float:
    """Inter-boot gap that still links two boots; floored by ``window_seconds`` so
    widening the window never makes the breaker *less* sensitive."""
    return float(max(1, window_seconds, max_gap_seconds))


def _chain_ending_at(boots: list[float], ts: float, gap: float) -> list[float]:
    """Unbroken chain of boots leading up to ``ts`` (oldest first): walks backwards
    while each gap stays within ``gap``; the first wider gap ends the chain (older
    boots are a resolved episode).  Empty when nothing is recent, which is how a healthy
    gateway forgets a loop."""
    chain: list[float] = []
    prev = ts
    for t in sorted(boots, reverse=True):
        if t > ts:  # clock moved backwards (NTP step, restored file): future entry is adjacent, not a break
            chain.append(t)
            continue
        if prev - t > gap:
            break
        chain.append(t)
        prev = t
    return chain[::-1]


def record_restart_interrupted_boot(
    window_seconds: int = DEFAULT_WINDOW_SECONDS, *, now: Optional[float] = None,
    max_gap_seconds: int = DEFAULT_MAX_GAP_SECONDS,
    reboot_grace_seconds: int = DEFAULT_REBOOT_GRACE_SECONDS,
    uptime: Optional[float] = None,
) -> list[float]:
    """Record a restart-interrupted boot; return the pruned chain + now (most recent
    last).  A persistence failure returns the in-memory list without raising.

    When this boot happened within ``reboot_grace_seconds`` of the host coming up it is part
    of a genuine host-reboot cascade (not a self-inflicted respawn loop): the prior chain is
    DROPPED and only this boot is kept, so a legitimate reboot can never trip the breaker.
    """
    ts = time.time() if now is None else now
    if _is_host_reboot_boot(reboot_grace_seconds, uptime=uptime):
        boots = [ts]
    else:
        boots = _chain_ending_at(_load_boots(), ts, _chain_gap(window_seconds, max_gap_seconds)) + [ts]
    _save_boots(boots[-_MAX_STORED_BOOTS:])
    return boots


def clear() -> None:
    """Remove the persisted boot log (used on clean shutdown / by tests)."""
    with contextlib.suppress(OSError):
        _state_path().unlink(missing_ok=True)


def check_and_record(
    max_restarts: int = DEFAULT_MAX_RESTARTS, window_seconds: int = DEFAULT_WINDOW_SECONDS, *,
    now: Optional[float] = None, max_gap_seconds: int = DEFAULT_MAX_GAP_SECONDS,
    reboot_grace_seconds: int = DEFAULT_REBOOT_GRACE_SECONDS,
) -> bool:
    """Gateway entry point: record this boot; True when the chain reached
    ``max_restarts`` and auto-resume should be SKIPPED.

    A boot within ``reboot_grace_seconds`` of the host coming up is a legitimate host-reboot
    cascade: it resets the chain and can never trip. Genuine crash loops on a long-lived host
    have high uptime and are still capped hard.
    """
    boots = record_restart_interrupted_boot(
        window_seconds, now=now, max_gap_seconds=max_gap_seconds,
        reboot_grace_seconds=reboot_grace_seconds,
    )
    tripped = max_restarts > 0 and len(boots) >= max_restarts
    if tripped:
        logger.warning(
            "Restart-loop breaker TRIPPED: %d chained restart-interrupted gateway boots (no gap wider than %ds; "
            "threshold %d). Skipping auto-resume to break a suspected SIGTERM-respawn loop (#30719, #81642). "
            "Restart-interrupted sessions stay resume-pending and will continue on the next real user message. "
            "If this is a false positive, delete %s.",
            len(boots), int(_chain_gap(window_seconds, max_gap_seconds)), max_restarts, _state_path(),
        )
    return tripped
