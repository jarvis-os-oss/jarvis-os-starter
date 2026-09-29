#!/usr/bin/env python3
"""Gateway-Health-Helfer (file-first Liveness pro Hermes-Profil).

Ergaenzt den Cockpit-Status-Collector um eine CLI. Die Gateways laufen
headless (kein HTTP-Port), also ist ein TCP-Connect kein verlaesslicher
Liveness-Test. Wahrheitsquelle ist die per-Profil-Datei gateway_state.json
(Feld gateway_state == "running" plus eine pid, die via /proc bestaetigt wird).

Profile werden data-driven aus dem Roster (dashboard/team_config.json, Schluessel
"key") oder aus --profiles gelesen, NICHT hart codiert.

Layout (Standard Hermes):
  default-Profil : <hermes_home>/gateway_state.json
  sub-Profil     : <hermes_home>/profiles/<key>/gateway_state.json

Subkommandos:
  status   Tabelle (ein Profil pro Zeile: RUNNING/STOPPED + pid).
  json     Maschinenlesbarer Status (fuers Dashboard / weitere Tools).
  check    Exit 0 wenn ALLE erwarteten Profile laufen, sonst Exit 1.

Rein lesend. stdlib-only. Startet/stoppt nichts (bewusst: Neustart ist Sache
des Watchdogs, um Doppel-Ownership zu vermeiden).

Exit-Codes:
  0  status/json ok, oder check: alle laufen
  1  check: mindestens ein erwartetes Profil laeuft nicht
  2  Nutzungs-/Eingabefehler
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _log(msg: str) -> None:
    print(msg, flush=True)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    # /proc ist Linux; fallback auf os.kill(0) fuer andere Plattformen.
    if os.path.isdir("/proc"):
        return os.path.isdir(f"/proc/{pid}")
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def state_file_for(hermes_home: str, key: str) -> str:
    if key == "default":
        return os.path.join(hermes_home, "gateway_state.json")
    return os.path.join(hermes_home, "profiles", key, "gateway_state.json")


def profile_status(hermes_home: str, key: str) -> dict:
    path = state_file_for(hermes_home, key)
    result = {"profile": key, "running": False, "pid": None, "detail": ""}
    if not os.path.isfile(path):
        result["detail"] = "kein gateway_state.json"
        return result
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        result["detail"] = f"state unlesbar: {e}"
        return result
    state = str(data.get("gateway_state", "")).lower()
    pid = data.get("pid")
    result["pid"] = pid if isinstance(pid, int) else None
    if state != "running":
        result["detail"] = f"gateway_state={state or '<leer>'}"
        return result
    if result["pid"] is None:
        result["detail"] = "running, aber keine pid"
        return result
    if _pid_alive(result["pid"]):
        result["running"] = True
        result["detail"] = f"running pid={result['pid']}"
    else:
        result["detail"] = f"pid {result['pid']} tot (stale state)"
    return result


def _roster_keys(roster_path: str) -> list[str]:
    with open(roster_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("agents", data) if isinstance(data, dict) else data
    keys = []
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("key"):
                keys.append(str(e["key"]))
    elif isinstance(entries, dict):
        keys = [str(k) for k in entries.keys()]
    return keys


def _resolve_profiles(args) -> list[str]:
    if args.profiles:
        return [p.strip() for p in args.profiles.split(",") if p.strip()]
    if args.roster and os.path.isfile(args.roster):
        try:
            keys = _roster_keys(args.roster)
            if keys:
                return keys
        except (json.JSONDecodeError, OSError):
            pass
    return ["default"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gateway-Health-Helfer (file-first)")
    default_home = os.environ.get("HERMES_HOME",
                                  os.path.join(os.path.expanduser("~"), ".hermes"))
    ap.add_argument("--hermes-home", default=default_home,
                    help="Hermes-Home (Default $HERMES_HOME oder ~/.hermes)")
    ap.add_argument("--profiles", default=None,
                    help="explizite Profil-Keys, kommagetrennt "
                         "(sonst aus --roster oder 'default')")
    ap.add_argument("--roster", default="dashboard/team_config.json",
                    help="Roster-JSON, aus dem die Profil-Keys gelesen werden")
    ap.add_argument("cmd", choices=["status", "json", "check"], help="Aktion")
    args = ap.parse_args(argv)

    profiles = _resolve_profiles(args)
    results = [profile_status(args.hermes_home, k) for k in profiles]

    if args.cmd == "json":
        _log(json.dumps({"hermes_home": args.hermes_home, "results": results},
                        indent=2))
        return 0

    if args.cmd == "status":
        for r in results:
            flag = "RUNNING" if r["running"] else "STOPPED"
            _log(f"{r['profile']:<20} {flag:<8} {r['detail']}")
        return 0

    # check
    down = [r["profile"] for r in results if not r["running"]]
    if down:
        _log(f"CHECK FEHLER: nicht laufend -> {', '.join(down)}")
        return 1
    _log(f"CHECK OK: alle {len(results)} Profile laufen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
