# Restart-loop breaker: host-reboot grace (opt-in core patch)

## What this fixes
The auto-resume restart-loop breaker in the Hermes runtime (`gateway/restart_loop_guard.py`)
trips when 3 restart-interrupted boots chain with no gap wider than 300s. That logic cannot tell a
self-inflicted respawn loop from a LEGITIMATE host reboot: after a VPS or kernel reboot several
supervised gateway slots can start in quick succession, the chain reaches 3, the breaker trips and
disables auto-resume. Agents then stay silent until `<HERMES_HOME>/gateway/restart_loop.json` is
deleted by hand.

## The fix
A boot that happens within `DEFAULT_REBOOT_GRACE_SECONDS` (120s) of the host coming up (read from
`/proc/uptime`) is part of a real host reboot. It does not extend the chain, it RESETS it to that one
boot. Safety properties:

- Real host reboot (uptime below 120s): the chain resets on every boot, auto-resume stays on.
- Real crash loop on a long-running host (high uptime): normal chaining, still capped hard at 3. No bypass.
- Unreadable `/proc/uptime`: fails CLOSED, behaves exactly like the stock breaker.
- `reboot_grace_seconds <= 0` disables the grace (stock behaviour).
- New parameters are optional keyword arguments, existing callers keep working unchanged.

## This is a patch for the Hermes runtime, not for the kit
The target file lives in the Hermes install (not tracked by this repo), so the fix ships as an
apply-ready patch. It is OPT-IN: pulling this repo changes nothing until you apply it yourself.

Files:
- `restart_loop_guard.reboot-grace.patch`: unified diff, `-p1`, against `gateway/restart_loop_guard.py`.
- `restart_loop_guard.patched.py`: full reference end version (used by `tests/test_loopbreaker_reboot_grace.py`).

Base: built against upstream `NousResearch/hermes-agent` main at commit
`5fc490e2b34123212d73ef316086f939567a725a`. If your install differs, `git apply --check` tells you.

## Apply and verify
Run inside your Hermes install directory:

    git apply --check -p1 /path/to/restart_loop_guard.reboot-grace.patch
    cp gateway/restart_loop_guard.py /root/restart_loop_guard.py.bak
    git apply -p1 /path/to/restart_loop_guard.reboot-grace.patch
    python3 -m py_compile gateway/restart_loop_guard.py
    diff gateway/restart_loop_guard.py /path/to/restart_loop_guard.patched.py

The only expected difference is ONE comment line in the `_chain_ending_at` docstring: the
reference copy has a dash replaced by a comma (to keep this repo free of dash characters).

Then restart the gateways. The call site needs no change, the grace is active by default.
Re-check after every runtime update: an update can overwrite the patched file.

## Test

    python3 -m unittest tests.test_loopbreaker_reboot_grace -v
