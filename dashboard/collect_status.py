#!/usr/bin/env python3
"""JARVIS-OS cockpit agent-status collector (host-side).

Writes a small, sanitised ``agent_status.json`` describing each agent
gateway's liveness, so the cockpit can render RUNNING/STOPPED without needing
the gateways to expose a TCP API port.

WHY THIS EXISTS
---------------
The cockpit's default liveness check (``cockpit_team.probe_status``) is a plain
TCP connect to ``127.0.0.1:<port>``. That only works if each Hermes gateway
runs its optional HTTP api_server on that port. In the default starter-kit
configuration ``gateway.api_server`` / per-profile ``api_server.enabled`` is
false, so the gateways run fine (Telegram etc.) but nothing listens on the
cockpit's port -> every agent shows STOPPED even though ``hermes -p <p> gateway
status`` reports running. Additionally the cockpit container has no host
network access to loopback ports even if they existed.

This collector reads the authoritative per-profile ``gateway_state.json`` that
Hermes writes, and confirms the recorded pid is actually alive. It runs on the
host (where both the Hermes state and /proc live) and drops the result into the
shared volume the cockpit already mounts. No secrets, no message content.
"""

import os
import json
import time

HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
ROSTER_PATH = os.environ.get(
    "AIOS_ROSTER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_config.json"),
)
OUTPUT_PATH = os.environ.get("AIOS_STATUS_FILE", "/opt/aios/logs/agent_status.json")
# A gateway_state.json older than this with no live pid is treated as stopped.
STALE_SECONDS = int(os.environ.get("AIOS_STATUS_STALE_SECONDS", "0"))  # 0 = pid-only


def _state_path(key):
    """Resolve the gateway_state.json path for a Hermes profile key.

    The default profile lives at the Hermes home root; named profiles live
    under ``profiles/<key>``.
    """
    if key == "default":
        return os.path.join(HERMES_HOME, "gateway_state.json")
    return os.path.join(HERMES_HOME, "profiles", key, "gateway_state.json")


def _pid_alive(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    return os.path.isdir("/proc/%d" % pid)


def _status_for(agent):
    key = agent.get("key")
    port = agent.get("port")
    if not key:
        return "planned"
    if not port:
        # No gateway port configured -> agent not deployed yet.
        return "planned"
    path = _state_path(key)
    try:
        with open(path) as fh:
            st = json.load(fh)
    except Exception:
        return "stopped"
    running = st.get("gateway_state") == "running" and _pid_alive(st.get("pid"))
    return "running" if running else "stopped"


def load_roster(path=ROSTER_PATH):
    try:
        with open(path) as fh:
            data = json.load(fh)
        return [a for a in data.get("agents", []) if isinstance(a, dict) and a.get("key")]
    except Exception:
        return []


def main():
    roster = load_roster()
    agents = {a["key"]: _status_for(a) for a in roster}
    out = {"generated_at": time.time(), "agents": agents}
    tmp = OUTPUT_PATH + ".tmp"
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, OUTPUT_PATH)
    print("wrote %s: %s" % (OUTPUT_PATH, json.dumps(agents)))


if __name__ == "__main__":
    main()
