#!/usr/bin/env python3
"""Product-/Price-Monitor: verfolgt beobachtete Preise gegen Zielwerte und
alarmiert, wenn ein Ziel erreicht ist.

Der Betreiber pflegt eine Watchlist (Name + Zielpreis). Fuer jeden Lauf wird
der aktuelle Preis GELIEFERT (per --price oder aus einer Snapshot-Datei), nicht
selbst aus dem Netz geholt: das eigentliche Abrufen ist site-spezifisch und
absichtlich NICHT Teil dieses generischen Bausteins (siehe README, ehrliche
Grenze). Das Tool fuehrt eine Preishistorie, erkennt Ziel-Unterschreitung und
gibt Alarme aus. stdlib-only, kein Netzzugriff.

SICHERHEIT / SHIPS DISABLED:
  * Ohne "enabled": true in der Config ist der Lauf ein No-Op (Exit 0, Hinweis).
  * Das Tool KAUFT NICHTS und loest keine Bestellung aus. Es meldet nur.

Nutzung:
  # aktuellen Preis fuer ein Item einspeisen und bewerten
  python3 scripts/price_monitor.py --config scripts/price_monitor.json \
      --item widget --price 19.99
  # oder eine ganze Preis-Snapshot-Datei bewerten {name: price}
  python3 scripts/price_monitor.py --config scripts/price_monitor.json \
      --snapshot prices.json

Exit-Codes:
  0  Lauf ok (auch deaktiviert; auch wenn kein Ziel erreicht)
  10 mindestens ein Zielpreis erreicht (fuer Alert-Gates)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg):
    print(f"[price-monitor {_now()}] {msg}", flush=True)


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_state(path):
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def _save_state(path, state):
    if not path:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def evaluate(config, prices, state=None):
    """prices: dict name->float. Gibt (alerts, updated_state) zurueck."""
    state = dict(state or {})
    items = {i["name"]: i for i in config.get("items", [])}
    alerts = []
    for name, price in prices.items():
        price = float(price)
        hist = state.get(name, {}).get("history", [])
        hist.append({"ts": _now(), "price": price})
        state[name] = {"last_price": price, "history": hist[-50:]}
        item = items.get(name)
        if item and "target_price" in item:
            target = float(item["target_price"])
            if price <= target:
                alerts.append({"name": name, "price": price, "target": target})
    return alerts, state


def main(argv=None):
    ap = argparse.ArgumentParser(description="Preis-Monitor gegen Zielwerte (meldet, kauft nie).")
    ap.add_argument("--config", required=True, help="Pfad zu price_monitor.json")
    ap.add_argument("--item", help="Name eines einzelnen Items")
    ap.add_argument("--price", type=float, help="aktueller Preis fuer --item")
    ap.add_argument("--snapshot", help="JSON-Datei {name: price} fuer mehrere Items")
    args = ap.parse_args(argv)

    config = load_config(args.config)
    if not config.get("enabled", False):
        _log("deaktiviert (enabled=false), No-Op")
        return 0

    prices = {}
    if args.snapshot:
        with open(args.snapshot, "r", encoding="utf-8") as fh:
            prices = {k: float(v) for k, v in json.load(fh).items()}
    elif args.item is not None and args.price is not None:
        prices = {args.item: args.price}
    else:
        ap.error("entweder --snapshot ODER --item + --price angeben")
        return 2

    state_path = config.get("state_file")
    state = _load_state(state_path)
    alerts, state = evaluate(config, prices, state)
    _save_state(state_path, state)

    for a in alerts:
        _log(f"ZIEL ERREICHT: {a['name']} bei {a['price']} (Ziel <= {a['target']})")
    if not alerts:
        _log(f"{len(prices)} Preis(e) bewertet, kein Ziel erreicht")
    return 10 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
