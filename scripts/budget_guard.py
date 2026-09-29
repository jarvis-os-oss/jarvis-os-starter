#!/usr/bin/env python3
"""LLM-Budget-Guard: pro-Agent- und Fleet-Ausgaben gegen Limits pruefen.

Ergaenzt das tiered-model-routing (das die Kosten SENKT) um die Kontroll-Seite:
es liest geschaetzte Ausgaben pro Agent aus einer Usage-Datei und meldet, wenn
ein Agent oder die ganze Flotte sein/ihr Budget im aktuellen Zeitfenster
ueberschreitet. Es DROSSELT nichts von selbst (kein Auto-Eingriff in fremde
Agenten); es liefert ein Urteil, das der Betreiber/sein Security-Agent
auswertet.

Usage-Eingabe (data-driven, provider-agnostisch): eine JSON-Datei mit
geschaetzten Kosten pro Agent im aktuellen Fenster, z.B.
  {"window": "2026-09", "spend": {"scout": 12.40, "assistant": 3.10}}
oder eine Liste von Records [{"agent": "scout", "cost": 12.40}, ...].
Wie diese Datei entsteht, ist instanzspezifisch (z.B. aus Provider-Rechnungen
oder aus fleet_cost_report.py); der Guard bewertet nur.

Config (siehe scripts/budget_guard.json), ships DISABLED:
  {
    "enabled": false,
    "currency": "USD",
    "fleet_limit": 100.0,
    "default_agent_limit": 20.0,
    "agent_limits": {"scout": 40.0, "assistant": 10.0},
    "warn_ratio": 0.8
  }

Exit-Codes:
  0  alles unter Limit (oder deaktiviert)
  1  mindestens ein Agent ODER die Flotte ueber Limit
  2  Nutzungs-/Konfigurationsfehler
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(msg, flush=True)


def _load_json(path: str) -> dict | list:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_usage(data) -> dict[str, float]:
    """Normalisiert verschiedene Usage-Formen zu {agent: cost}."""
    spend: dict[str, float] = {}
    if isinstance(data, dict) and isinstance(data.get("spend"), dict):
        for agent, cost in data["spend"].items():
            try:
                spend[str(agent)] = spend.get(str(agent), 0.0) + float(cost)
            except (TypeError, ValueError):
                continue
    elif isinstance(data, list):
        for rec in data:
            if not isinstance(rec, dict):
                continue
            agent = rec.get("agent") or rec.get("name")
            cost = rec.get("cost", rec.get("spend", rec.get("estimated_cost")))
            if agent is None or cost is None:
                continue
            try:
                spend[str(agent)] = spend.get(str(agent), 0.0) + float(cost)
            except (TypeError, ValueError):
                continue
    return spend


def evaluate(config: dict, usage) -> tuple[int, list[dict]]:
    spend = _parse_usage(usage)
    currency = config.get("currency", "USD")
    fleet_limit = config.get("fleet_limit")
    default_limit = config.get("default_agent_limit")
    agent_limits = config.get("agent_limits", {}) or {}
    warn_ratio = float(config.get("warn_ratio", 0.8))

    findings = []
    breached = False

    for agent in sorted(spend):
        cost = spend[agent]
        limit = agent_limits.get(agent, default_limit)
        status = "OK"
        if limit is not None:
            limit = float(limit)
            if cost > limit:
                status = "OVER"
                breached = True
            elif limit > 0 and cost >= warn_ratio * limit:
                status = "WARN"
        findings.append({"scope": agent, "cost": round(cost, 4),
                         "limit": limit, "status": status})
        line = f"  {agent:<20} {cost:>10.2f} {currency}"
        if limit is not None:
            line += f"  / limit {limit:.2f}  [{status}]"
        else:
            line += "  (kein Limit)"
        _log(line)

    total = round(sum(spend.values()), 4)
    fleet_status = "OK"
    if fleet_limit is not None:
        fleet_limit = float(fleet_limit)
        if total > fleet_limit:
            fleet_status = "OVER"
            breached = True
        elif fleet_limit > 0 and total >= warn_ratio * fleet_limit:
            fleet_status = "WARN"
    findings.append({"scope": "__fleet__", "cost": total,
                     "limit": fleet_limit, "status": fleet_status})
    _log(f"  {'FLEET':<20} {total:>10.2f} {currency}"
         + (f"  / limit {fleet_limit:.2f}  [{fleet_status}]"
            if fleet_limit is not None else "  (kein Limit)"))

    return (1 if breached else 0), findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LLM-Budget-Guard")
    ap.add_argument("--config", required=True, help="Pfad zur budget_guard.json")
    ap.add_argument("--usage", required=True, help="Pfad zur Usage-JSON")
    ap.add_argument("--status-file", default=None,
                    help="optional: Ergebnis als JSON hierhin schreiben")
    args = ap.parse_args(argv)

    for label, path in (("Config", args.config), ("Usage", args.usage)):
        if not os.path.isfile(path):
            _log(f"{label} nicht gefunden: {path}")
            return 2
    try:
        config = _load_json(args.config)
        usage = _load_json(args.usage)
    except (json.JSONDecodeError, OSError) as e:
        _log(f"Eingabe ungueltig: {e}")
        return 2
    if not isinstance(config, dict):
        _log("Config muss ein JSON-Objekt sein")
        return 2

    if not config.get("enabled", False):
        _log("Budget-Guard deaktiviert (enabled=false), keine Bewertung")
        return 0

    _log(f"Budget-Bewertung {_now()}:")
    rc, findings = evaluate(config, usage)

    if args.status_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.status_file)),
                        exist_ok=True)
            with open(args.status_file, "w", encoding="utf-8") as fh:
                json.dump({"checked_at": _now(), "breached": bool(rc),
                           "findings": findings}, fh, indent=2)
        except OSError as e:
            _log(f"Statusdatei nicht schreibbar: {e}")

    _log("ERGEBNIS: " + ("LIMIT UEBERSCHRITTEN" if rc else "alles im Rahmen"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
