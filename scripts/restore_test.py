#!/usr/bin/env python3
"""Restore-Test fuer Backups (ein Backup ist nur real, wenn es zuruueckspielt).

Ein Backup, das nie zurueckgespielt wurde, ist eine Hoffnung, kein Backup.
Dieses Tool nimmt konfigurierte Backup-Quellen, spielt sie in ein WEGWERF-Ziel
(temporaeres Verzeichnis) zurueck und prueft, dass die Wiederherstellung
plausibel ist. Es fasst die produktiven Daten NIE an.

Unterstuetzte Ziel-Typen (data-driven, keine Instanz-Spezifika):
  tarball  Ein .tar/.tar.gz-Archiv: es wird in ein Temp-Verzeichnis extrahiert
           und geprueft, ob mindestens `min_files` Dateien und optional die in
           `expect_members` gelisteten Pfade enthalten sind.
  sqlite   Ein Verzeichnis mit SQLite-Backups: das juengste passende Backup wird
           in eine Temp-Datei kopiert und per PRAGMA integrity_check geprueft.

Alles stdlib-only. Ships DISABLED: ohne "enabled": true in der Config tut das
Tool nichts (Exit 0 mit Hinweis), damit eine frische Installation nichts
ungefragt startet.

Config (siehe scripts/restore_test.json):
  {
    "enabled": false,
    "status_file": "REPLACE_WITH_STATUS_PATH/restore_test_status.json",
    "targets": [
      {"name": "example-archive", "type": "tarball",
       "path": "REPLACE_WITH_BACKUP_DIR/example.tar.gz",
       "min_files": 1, "expect_members": []},
      {"name": "example-db", "type": "sqlite",
       "backup_dir": "REPLACE_WITH_BACKUP_DIR/db_backups",
       "glob": "*.ok"}
    ]
  }

Exit-Codes:
  0  alle Ziele bestanden (oder Tool deaktiviert)
  1  mindestens ein Ziel FEHLGESCHLAGEN
  2  Nutzungs-/Konfigurationsfehler
"""
from __future__ import annotations

import argparse
import fnmatch
import glob as globmod
import json
import os
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"[restore-test {_now()}] {msg}", flush=True)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _test_tarball(target: dict) -> tuple[bool, str]:
    path = target.get("path", "")
    if not path or not os.path.isfile(path):
        return False, f"Archiv fehlt: {path}"
    min_files = int(target.get("min_files", 1))
    expect = list(target.get("expect_members", []))
    tmp = tempfile.mkdtemp(prefix="restoretest_")
    try:
        try:
            with tarfile.open(path, "r:*") as tf:
                members = tf.getnames()
                # Sichere Extraktion: keine absoluten Pfade / Traversal zulassen.
                safe = [m for m in tf.getmembers()
                        if not (m.name.startswith("/") or ".." in m.name.split("/"))]
                tf.extractall(tmp, members=safe)
        except (tarfile.TarError, OSError) as e:
            return False, f"Extraktion fehlgeschlagen: {e}"
        extracted = []
        for base, _dirs, names in os.walk(tmp):
            for n in names:
                extracted.append(os.path.relpath(os.path.join(base, n), tmp))
        if len(extracted) < min_files:
            return False, f"nur {len(extracted)} Dateien, erwartet >= {min_files}"
        for exp in expect:
            if not any(fnmatch.fnmatch(f, exp) or f == exp for f in members):
                return False, f"erwartetes Member fehlt: {exp}"
        return True, f"{len(extracted)} Dateien wiederhergestellt"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _integrity_ok(db_path: str) -> bool:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=15)
    except sqlite3.Error:
        return False
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return bool(rows) and (rows[0][0] or "").lower() == "ok"
    except sqlite3.DatabaseError:
        return False
    finally:
        conn.close()


def _test_sqlite(target: dict) -> tuple[bool, str]:
    backup_dir = target.get("backup_dir", "")
    pattern = target.get("glob", "*.ok")
    if not backup_dir or not os.path.isdir(backup_dir):
        return False, f"Backup-Verzeichnis fehlt: {backup_dir}"
    candidates = sorted(globmod.glob(os.path.join(backup_dir, pattern)), reverse=True)
    if not candidates:
        return False, f"kein Backup passend zu {pattern}"
    newest = candidates[0]
    tmp = tempfile.mkdtemp(prefix="restoretest_")
    try:
        dst = os.path.join(tmp, "restored.db")
        try:
            shutil.copy2(newest, dst)
        except OSError as e:
            return False, f"Kopie fehlgeschlagen: {e}"
        if not _integrity_ok(dst):
            return False, f"integrity_check FEHLGESCHLAGEN fuer {os.path.basename(newest)}"
        return True, f"restore+integrity ok ({os.path.basename(newest)})"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


HANDLERS = {"tarball": _test_tarball, "sqlite": _test_sqlite}


def run(config: dict) -> int:
    if not config.get("enabled", False):
        _log("deaktiviert (enabled=false), nichts zu tun")
        return 0
    targets = config.get("targets", [])
    if not targets:
        _log("keine Ziele konfiguriert")
        return 0
    results = []
    all_ok = True
    for t in targets:
        name = t.get("name", "?")
        typ = t.get("type", "")
        handler = HANDLERS.get(typ)
        if handler is None:
            ok, detail = False, f"unbekannter Typ: {typ}"
        else:
            ok, detail = handler(t)
        all_ok = all_ok and ok
        _log(f"{name}: {'OK' if ok else 'FEHLER'} - {detail}")
        results.append({"name": name, "type": typ, "ok": ok, "detail": detail})
    status_file = config.get("status_file")
    if status_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(status_file)), exist_ok=True)
            with open(status_file, "w", encoding="utf-8") as fh:
                json.dump({"checked_at": _now(), "all_ok": all_ok,
                           "results": results}, fh, indent=2)
        except OSError as e:
            _log(f"Statusdatei konnte nicht geschrieben werden: {e}")
    return 0 if all_ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Restore-Test fuer Backups")
    ap.add_argument("--config", required=True, help="Pfad zur restore_test.json")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.config):
        _log(f"Config nicht gefunden: {args.config}")
        return 2
    try:
        config = load_config(args.config)
    except (json.JSONDecodeError, OSError) as e:
        _log(f"Config ungueltig: {e}")
        return 2
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
