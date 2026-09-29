#!/usr/bin/env python3
"""Tests for scripts/state_guardian.py.

Realistic: creates real SQLite DBs in a temp dir, corrupts one byte-wise, and
asserts the guardian blocks a blind start and restores cleanly from a backup.
No mocks, real behaviour. Runs under `python3 -m unittest discover -s tests`.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import state_guardian as sg  # noqa: E402


def _make_db(path: str, rows: int = 50) -> None:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(f"row-{i}",) for i in range(rows)])
    conn.commit()
    conn.close()


def _corrupt(path: str) -> None:
    """Overwrites the SQLite header magic string, guaranteeing a corrupt DB."""
    with open(path, "r+b") as f:
        f.write(b"XXXXXXXXXXXXXXXX")  # destroys 'SQLite format 3\0'


def _count(path: str) -> int:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    finally:
        conn.close()


class StateGuardianTest(unittest.TestCase):
    def test_healthy_db_passes_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db, rows=50)
            self.assertTrue(sg.integrity_ok(db))

    def test_check_command_exit0_on_healthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            args = sg.build_parser().parse_args(["--db", db, "check"])
            self.assertEqual(sg.cmd_check(args), 0)

    def test_backup_created_and_healthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            bpath = sg.make_backup(db)
            self.assertTrue(bpath and os.path.isfile(bpath))
            self.assertTrue(sg.integrity_ok(bpath))

    def test_guard_healthy_exit0_and_rotates_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            gargs = sg.build_parser().parse_args(["--db", db, "guard"])
            self.assertEqual(sg.cmd_guard(gargs), 0)
            self.assertEqual(sg.cmd_guard(gargs), 0)
            n_backups = len([f for f in os.listdir(os.path.join(tmp, "backups"))
                             if f.endswith(sg.BACKUP_SUFFIX)])
            self.assertGreaterEqual(n_backups, 2)

    def test_corrupt_db_fails_integrity_and_check_exit3(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            _corrupt(db)
            for side in ("-wal", "-shm"):
                p = db + side
                if os.path.exists(p):
                    os.remove(p)
            self.assertFalse(sg.integrity_ok(db))
            args = sg.build_parser().parse_args(["--db", db, "check"])
            self.assertEqual(sg.cmd_check(args), 3)

    def test_backup_refused_on_corrupt_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            _corrupt(db)
            args = sg.build_parser().parse_args(["--db", db, "backup"])
            self.assertEqual(sg.cmd_backup(args), 3)

    def test_guard_auto_restores_corrupt_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db, rows=50)
            # take a healthy backup first
            sg.make_backup(db)
            _corrupt(db)
            for side in ("-wal", "-shm"):
                p = db + side
                if os.path.exists(p):
                    os.remove(p)
            gargs = sg.build_parser().parse_args(["--db", db, "guard"])
            self.assertEqual(sg.cmd_guard(gargs), 0)
            self.assertTrue(sg.integrity_ok(db))
            self.assertEqual(_count(db), 50)
            corrupt_saved = any(f.startswith("state.db.corrupt-") for f in os.listdir(tmp))
            self.assertTrue(corrupt_saved)

    def test_restore_without_backup_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "state.db")
            _make_db(db)
            _corrupt(db)
            args = sg.build_parser().parse_args(["--db", db, "restore"])
            self.assertEqual(sg.cmd_restore(args), 3)


if __name__ == "__main__":
    unittest.main()
