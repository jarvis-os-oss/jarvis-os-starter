#!/usr/bin/env python3
"""Fleet-Kostenreport: aggregiert geschaetzte LLM-Kosten pro Agent.

Liest Usage-Records aus einer oder mehreren JSON-Dateien (z.B. eine je Agent
oder eine Sammel-Datei) und erzeugt einen aggregierten Kostenreport pro Agent
plus Fleet-Summe. Reine Observability, aendert nichts. stdlib-only.

Eingabeformate (tolerant, data-driven):
  * Objekt mit "records": [ {"agent": "...", "cost": 1.2, "ts": "..."}, ... ]
  * Liste von Records [ {"agent": "...", "cost": 1.2}, ... ]
  * Objekt {"spend": {"agent": cost, ...}} (bereits aggregiert)
Feldnamen fuer die Kosten: cost | spend | estimated_cost. Fuer den Agenten:
agent | name | profile. Ein optionales Fenster-Feld (window/period) wird nur
uebernommen, wenn vorhanden.

Agenten-Namensaufloesung ist roster-basiert (dashboard/team_config.json), NICHT
hart codiert: unbekannte Keys erscheinen unveraendert.

Ausgabe: Text-Tabelle (Default) oder --format json.

Exit-Codes:
  0  Report erzeugt
  2  Nutzungs-/Eingabefehler
"""
from __future__ import annotations

import argparse
import glob as globmod
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


COST_KEYS = ("cost", "spend", "estimated_cost")
AGENT_KEYS = ("agent", "name", "profile")


def _load(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _records_from(data):
    """Normalisiert Eingabeformen zu einer Liste von (agent, cost)-Tupeln."""
    out = []
    if isinstance(data, dict) and isinstance(data.get("spend"), dict):
        for agent, cost in data["spend"].items():
            try:
                out.append((str(agent), float(cost)))
            except (TypeError, ValueError):
                continue
        return out
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        records = data["records"]
    elif isinstance(data, list):
        records = data
    else:
        records = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        agent = next((rec[k] for k in AGENT_KEYS if k in rec), None)
        cost = next((rec[k] for k in COST_KEYS if k in rec), None)
        if agent is None or cost is None:
            continue
        try:
            out.append((str(agent), float(cost)))
        except (TypeError, ValueError):
            continue
    return out


def _roster_names(roster_path: str) -> dict[str, str]:
    names = {}
    try:
        data = _load(roster_path)
    except (json.JSONDecodeError, OSError):
        return names
    entries = data.get("agents", data) if isinstance(data, dict) else data
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("key"):
                names[str(e["key"])] = str(e.get("name", e["key"]))
    elif isinstance(entries, dict):
        for k, v in entries.items():
            if isinstance(v, dict):
                names[str(k)] = str(v.get("name", k))
    return names


def _expand(inputs: list[str]) -> list[str]:
    paths = []
    for inp in inputs:
        if os.path.isdir(inp):
            paths.extend(sorted(globmod.glob(os.path.join(inp, "*.json"))))
        elif any(ch in inp for ch in "*?["):
            paths.extend(sorted(globmod.glob(inp, recursive=True)))
        else:
            paths.append(inp)
    return [p for p in paths if os.path.isfile(p)]


def build_report(paths: list[str], roster: dict[str, str]) -> dict:
    by_agent: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for path in paths:
        try:
            data = _load(path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: {path} uebersprungen ({e})", flush=True)
            continue
        for agent, cost in _records_from(data):
            by_agent[agent] += cost
            counts[agent] += 1
    agents = []
    for key in sorted(by_agent, key=lambda k: by_agent[k], reverse=True):
        agents.append({
            "key": key,
            "name": roster.get(key, key),
            "cost": round(by_agent[key], 4),
            "records": counts[key],
        })
    total = round(sum(by_agent.values()), 4)
    return {"generated_at": _now(), "fleet_total": total, "agents": agents}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fleet-Kostenreport")
    ap.add_argument("paths", nargs="+",
                    help="Usage-JSON-Dateien, Globs oder Verzeichnisse")
    ap.add_argument("--roster", default="dashboard/team_config.json",
                    help="Roster fuer die Namensaufloesung")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--currency", default="USD")
    args = ap.parse_args(argv)

    paths = _expand(args.paths)
    if not paths:
        print("keine Eingabedateien gefunden", flush=True)
        return 2
    roster = _roster_names(args.roster) if os.path.isfile(args.roster) else {}
    report = build_report(paths, roster)

    if args.format == "json":
        print(json.dumps(report, indent=2))
        return 0

    print(f"Fleet-Kostenreport ({report['generated_at']}):")
    print(f"  {'Agent':<24} {'Kosten':>12} {'Records':>9}")
    for a in report["agents"]:
        print(f"  {a['name']:<24} {a['cost']:>12.2f} {a['records']:>9}")
    print(f"  {'-' * 24} {'-' * 12} {'-' * 9}")
    print(f"  {'FLEET':<24} {report['fleet_total']:>12.2f} {args.currency}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
