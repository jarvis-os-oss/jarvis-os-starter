#!/usr/bin/env python3
"""Memory-Snapshot-Backup: erstellt versionierte, gepackte Snapshots der
Agent-Memory-Schicht und haelt eine Retention ein.

Die Memory-Dateien eines Agenten (Notizen/Profil/Erinnerungen) sind wertvoll
und aendern sich staendig. Dieses Tool packt konfigurierte Memory-Quellen in
einen zeitgestempelten tar.gz-Snapshot in einem Ziel-Ordner und loescht
Snapshots, die aelter als die Retention sind. stdlib-only (tarfile), kein
Netzzugriff.

SICHERHEIT / SHIPS DISABLED:
  * Ohne "enabled": true in der Config ist der Lauf ein No-Op (Exit 0, Hinweis).
  * Das Tool schreibt NUR in den konfigurierten dest-Ordner. Quellen werden
    nur gelesen. Retention-Loeschung betrifft ausschliesslich eigene Snapshots
    (Praefix "memsnap-") im dest-Ordner, nichts anderes.

Nutzung:
  python3 scripts/memory_snapshot.py --config scripts/memory_snapshot.json
  python3 scripts/memory_snapshot.py --config scripts/memory_snapshot.json --list

Config (siehe scripts/memory_snapshot.json):
  {
    "enabled": false,
    "sources": ["REPLACE_WITH_PROFILE_HOME/memory", "REPLACE_WITH_PROFILE_HOME/user"],
    "dest": "REPLACE_WITH_BACKUP_DIR/memory-snapshots",
    "retention_days": 30
  }

Exit-Codes:
  0  ok (auch deaktiviert)
  2  Nutzungs-/Konfigurationsfehler
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import time
from datetime import datetime, timezone

_PREFIX = "memsnap-"


def _now_tag():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[memory-snapshot {ts}] {msg}", flush=True)


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def create_snapshot(sources, dest):
    """Packt existierende Quellen in einen tar.gz-Snapshot. Gibt Pfad zurueck."""
    os.makedirs(dest, exist_ok=True)
    tag = _now_tag()
    out = os.path.join(dest, f"{_PREFIX}{tag}.tar.gz")
    present = [s for s in sources if os.path.exists(s)]
    with tarfile.open(out, "w:gz") as tar:
        for src in present:
            tar.add(src, arcname=os.path.basename(os.path.normpath(src)))
    return out, present


def prune(dest, retention_days):
    """Loescht eigene Snapshots aelter als retention_days. Gibt Liste zurueck."""
    if retention_days is None or retention_days <= 0:
        return []
    cutoff = time.time() - retention_days * 86400
    removed = []
    for name in os.listdir(dest):
        if not (name.startswith(_PREFIX) and name.endswith(".tar.gz")):
            continue
        p = os.path.join(dest, name)
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
                removed.append(p)
        except OSError:
            pass
    return removed


def list_snapshots(dest):
    if not os.path.isdir(dest):
        return []
    return sorted(n for n in os.listdir(dest)
                  if n.startswith(_PREFIX) and n.endswith(".tar.gz"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Versionierte Snapshots der Agent-Memory.")
    ap.add_argument("--config", required=True, help="Pfad zu memory_snapshot.json")
    ap.add_argument("--list", action="store_true", help="vorhandene Snapshots listen und beenden")
    args = ap.parse_args(argv)

    config = load_config(args.config)
    dest = config.get("dest")

    if args.list:
        for n in list_snapshots(dest or "."):
            print(n)
        return 0

    if not config.get("enabled", False):
        _log("deaktiviert (enabled=false), No-Op")
        return 0

    sources = config.get("sources") or []
    if not dest or not sources:
        _log("Konfiguration unvollstaendig (sources/dest fehlen)")
        return 2

    out, present = create_snapshot(sources, dest)
    _log(f"Snapshot erstellt: {out} ({len(present)} Quelle(n) gepackt)")
    removed = prune(dest, config.get("retention_days"))
    if removed:
        _log(f"{len(removed)} alte(r) Snapshot(s) nach Retention geloescht")
    return 0


if __name__ == "__main__":
    sys.exit(main())
