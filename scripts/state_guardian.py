#!/usr/bin/env python3
"""State-Guardian fuer Hermes state.db (Reboot-Kaskade-Schutz).

Root-Cause (Vorfall 23.9.2026): Ein harter Abbruch (VPS-Reboot, OOM-Kill,
SIGKILL mitten im Schreiben) laesst die WAL der state.db ungecheckpointed
zurueck. Die DB wird strukturell korrupt. Der Watchdog startet das Gateway
danach BLIND neu, Hermes oeffnet die korrupte DB, crasht, der Watchdog startet
erneut: eine Crash-Loop (die Reboot-Kaskade). Es gab weder eine
Integritaetspruefung vor dem Start noch ein konsistentes Backup zum
Zurueckspielen.

Dieser Guardian schliesst genau diese Luecke. Er wird VOR jedem Gateway-Start
pro Profil aufgerufen und macht:

  check   PRAGMA integrity_check + quick_check. Exit 0 = gesund, 3 = korrupt.
  backup  Nur wenn gesund: konsistentes Online-Hot-Backup (sqlite3 .backup,
          NICHT cp) mit Rotation. Vorher wird die WAL sauber gecheckpointed.
  guard   check; bei OK ein Backup rotieren und Exit 0 (Start erlaubt).
          Bei Korruption: KEIN Blind-Start. Auto-Restore aus dem juengsten
          gueltigen Backup versuchen und erneut pruefen. Erfolg -> Exit 0,
          Misserfolg -> Exit 3 (Aufrufer MUSS den Start abbrechen + alarmieren).
  restore Manuell aus dem juengsten (oder angegebenen) gueltigen Backup
          zuruecksichern. Legt vorher eine .corrupt-Kopie des Ist-Standes an.

Design:
  * stdlib-only (python3 sqlite3), kein sqlite3-CLI noetig.
  * Idempotent, sicher wiederholbar. Zerstoert nie ein Original ohne vorher
    eine .corrupt-<ts>-Kopie zu ziehen.
  * Keine Em-Dashes, deutschsprachige Logausgabe (eine Statuszeile je Aktion).

Exit-Codes:
  0  Aktion erfolgreich / DB gesund (Start erlaubt)
  2  Nutzungs-/Argumentfehler oder DB-Datei fehlt
  3  DB korrupt und NICHT automatisch wiederherstellbar (Start abbrechen)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone

DEFAULT_KEEP = 7  # Anzahl rotierender Backups, die behalten werden
BACKUP_SUFFIX = ".ok"  # Backups heissen state.db.<utcts>.ok


def _ts() -> str:
    # Millisekunden-genau, damit zwei Backups in derselben Sekunde (schnelle
    # Restart-Zyklen) nicht denselben Dateinamen bekommen und sich ueberschreiben.
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def _log(msg: str) -> None:
    print(f"[state-guardian {datetime.now(timezone.utc).strftime('%H:%M:%S')}Z] {msg}",
          flush=True)


def _backup_dir(db_path: str) -> str:
    d = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(d, exist_ok=True)
    return d


def integrity_ok(db_path: str) -> bool:
    """True wenn quick_check UND integrity_check 'ok' liefern.

    Ein korrupter DB-Header oder eine kaputte Struktur fuehrt entweder zu
    DatabaseError beim Oeffnen/Abfragen oder zu einer Nicht-'ok'-Antwort.
    Beides werten wir als korrupt.
    """
    if not os.path.isfile(db_path):
        return False
    try:
        # ro-Modus: die Pruefung darf die DB nie veraendern.
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=15)
    except sqlite3.Error:
        return False
    try:
        for pragma in ("quick_check", "integrity_check"):
            try:
                rows = conn.execute(f"PRAGMA {pragma}").fetchall()
            except sqlite3.DatabaseError:
                return False
            if not rows or (rows[0][0] or "").lower() != "ok":
                return False
        return True
    finally:
        conn.close()


def _rotate(backup_dir: str, keep: int) -> None:
    backups = sorted(
        (f for f in os.listdir(backup_dir) if f.endswith(BACKUP_SUFFIX)),
        reverse=True,
    )
    for stale in backups[keep:]:
        try:
            os.remove(os.path.join(backup_dir, stale))
        except OSError:
            pass


def make_backup(db_path: str, keep: int = DEFAULT_KEEP) -> str | None:
    """Konsistentes Online-Hot-Backup via sqlite3-Backup-API.

    Vorher wird die WAL in die Haupt-DB gecheckpointed (TRUNCATE), damit das
    Backup den vollstaendigen Stand enthaelt. Gibt den Backup-Pfad zurueck oder
    None bei Fehler. Ruft NICHT selbst integrity_check auf; der Aufrufer stellt
    sicher, dass die Quelle gesund ist.
    """
    if not os.path.isfile(db_path):
        _log(f"backup uebersprungen: {db_path} existiert nicht")
        return None
    backup_dir = _backup_dir(db_path)
    dst = os.path.join(backup_dir, f"{os.path.basename(db_path)}.{_ts()}{BACKUP_SUFFIX}")
    try:
        src = sqlite3.connect(db_path, timeout=30)
        try:
            # WAL sauber einarbeiten, damit das Backup nichts verpasst.
            src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            dest = sqlite3.connect(dst)
            try:
                src.backup(dest)
            finally:
                dest.close()
        finally:
            src.close()
    except sqlite3.Error as e:
        _log(f"backup FEHLGESCHLAGEN: {e}")
        if os.path.exists(dst):
            try:
                os.remove(dst)
            except OSError:
                pass
        return None
    # Gegenpruefung: das frische Backup muss selbst gesund sein.
    if not integrity_ok(dst):
        _log("backup verworfen: frisches Backup besteht integrity_check NICHT")
        try:
            os.remove(dst)
        except OSError:
            pass
        return None
    _rotate(backup_dir, keep)
    _log(f"backup ok: {dst}")
    return dst


def latest_good_backup(db_path: str) -> str | None:
    backup_dir = _backup_dir(db_path)
    candidates = sorted(
        (os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
         if f.endswith(BACKUP_SUFFIX)),
        reverse=True,
    )
    for cand in candidates:
        if integrity_ok(cand):
            return cand
    return None


def restore(db_path: str, from_backup: str | None = None) -> bool:
    """Sichert die aktuelle (mutmasslich korrupte) DB als .corrupt-<ts> weg und
    kopiert das juengste gueltige Backup an ihre Stelle. Danach Gegenpruefung.
    """
    src = from_backup or latest_good_backup(db_path)
    if not src or not os.path.isfile(src):
        _log("restore nicht moeglich: kein gueltiges Backup gefunden")
        return False
    if not integrity_ok(src):
        _log(f"restore abgebrochen: gewaehltes Backup ist selbst korrupt ({src})")
        return False
    # Ist-Stand (korrupt) beweissicher wegsichern, nie einfach loeschen.
    if os.path.isfile(db_path):
        corrupt_copy = f"{db_path}.corrupt-{_ts()}"
        try:
            shutil.copy2(db_path, corrupt_copy)
            _log(f"korrupten Stand gesichert: {corrupt_copy}")
        except OSError as e:
            _log(f"restore abgebrochen: konnte Ist-Stand nicht sichern ({e})")
            return False
    # Verwaiste WAL/SHM entfernen, damit sie nicht auf die neue DB angewendet werden.
    for side in ("-wal", "-shm"):
        p = db_path + side
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    try:
        shutil.copy2(src, db_path)
    except OSError as e:
        _log(f"restore FEHLGESCHLAGEN beim Kopieren: {e}")
        return False
    if not integrity_ok(db_path):
        _log("restore FEHLGESCHLAGEN: wiederhergestellte DB besteht Pruefung nicht")
        return False
    _log(f"restore ok: {src} -> {db_path}")
    return True


def cmd_check(args) -> int:
    if not os.path.isfile(args.db):
        _log(f"check: {args.db} existiert nicht")
        return 2
    if integrity_ok(args.db):
        _log("check: DB gesund")
        return 0
    _log("check: DB KORRUPT")
    return 3


def cmd_backup(args) -> int:
    if not integrity_ok(args.db):
        _log("backup abgebrochen: Quelle ist korrupt (kein Backup einer kaputten DB)")
        return 3
    return 0 if make_backup(args.db, args.keep) else 2


def cmd_guard(args) -> int:
    """Der Aufruf VOR dem Gateway-Start. Exit 0 = Start erlaubt."""
    if not os.path.isfile(args.db):
        # Frische Installation ohne DB: Start erlauben, Hermes legt sie an.
        _log("guard: keine DB vorhanden, Start erlaubt (Neuanlage)")
        return 0
    if integrity_ok(args.db):
        make_backup(args.db, args.keep)  # bester Zeitpunkt: DB ist gesund
        _log("guard: DB gesund, Start erlaubt")
        return 0
    _log("guard: DB KORRUPT, Blind-Start blockiert, versuche Auto-Restore")
    if restore(args.db):
        _log("guard: Auto-Restore erfolgreich, Start erlaubt")
        return 0
    _log("guard: Auto-Restore FEHLGESCHLAGEN, Start MUSS abgebrochen werden")
    return 3


def cmd_restore(args) -> int:
    return 0 if restore(args.db, args.from_backup) else 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="State-Guardian fuer Hermes state.db")
    p.add_argument("--db", required=True, help="Pfad zur state.db")
    p.add_argument("--keep", type=int, default=DEFAULT_KEEP,
                   help=f"Anzahl rotierender Backups (Default {DEFAULT_KEEP})")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Integritaet pruefen (Exit 3 = korrupt)")
    sub.add_parser("backup", help="Konsistentes Hot-Backup ziehen (nur wenn gesund)")
    sub.add_parser("guard", help="Vor Gateway-Start: pruefen, backup, ggf. Auto-Restore")
    rp = sub.add_parser("restore", help="Aus juengstem gueltigen Backup zuruecksichern")
    rp.add_argument("--from-backup", dest="from_backup", default=None,
                    help="Optional: konkreter Backup-Pfad statt juengstem gueltigen")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return {
        "check": cmd_check,
        "backup": cmd_backup,
        "guard": cmd_guard,
        "restore": cmd_restore,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
