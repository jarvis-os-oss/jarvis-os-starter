#!/usr/bin/env python3
"""Tests for scripts/restore_test.py. Real tar + real sqlite, no mocks."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tarfile
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import restore_test as rt  # noqa: E402


def _make_tar(path: str, n: int = 3) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for i in range(n):
            data = f"content-{i}".encode()
            info = tarfile.TarInfo(name=f"file_{i}.txt")
            info.size = len(data)
            import io
            tf.addfile(info, io.BytesIO(data))


def _make_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO t (id) VALUES (?)", [(i,) for i in range(5)])
    conn.commit()
    conn.close()


class RestoreTestTest(unittest.TestCase):
    def test_disabled_is_noop_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "c.json")
            with open(cfg, "w") as fh:
                json.dump({"enabled": False, "targets": []}, fh)
            self.assertEqual(rt.main(["--config", cfg]), 0)

    def test_tarball_restore_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc = os.path.join(tmp, "a.tar.gz")
            _make_tar(arc, 3)
            cfg = os.path.join(tmp, "c.json")
            with open(cfg, "w") as fh:
                json.dump({"enabled": True, "status_file": os.path.join(tmp, "s.json"),
                           "targets": [{"name": "a", "type": "tarball",
                                        "path": arc, "min_files": 3,
                                        "expect_members": ["file_0.txt"]}]}, fh)
            self.assertEqual(rt.main(["--config", cfg]), 0)
            with open(os.path.join(tmp, "s.json")) as fh:
                status = json.load(fh)
            self.assertTrue(status["all_ok"])

    def test_tarball_missing_member_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc = os.path.join(tmp, "a.tar.gz")
            _make_tar(arc, 1)
            cfg = os.path.join(tmp, "c.json")
            with open(cfg, "w") as fh:
                json.dump({"enabled": True,
                           "targets": [{"name": "a", "type": "tarball",
                                        "path": arc, "min_files": 5}]}, fh)
            self.assertEqual(rt.main(["--config", cfg]), 1)

    def test_sqlite_restore_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bdir = os.path.join(tmp, "bk")
            os.makedirs(bdir)
            _make_db(os.path.join(bdir, "state.db.20260101.ok"))
            cfg = os.path.join(tmp, "c.json")
            with open(cfg, "w") as fh:
                json.dump({"enabled": True,
                           "targets": [{"name": "db", "type": "sqlite",
                                        "backup_dir": bdir, "glob": "*.ok"}]}, fh)
            self.assertEqual(rt.main(["--config", cfg]), 0)

    def test_sqlite_no_backup_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            bdir = os.path.join(tmp, "bk")
            os.makedirs(bdir)
            cfg = os.path.join(tmp, "c.json")
            with open(cfg, "w") as fh:
                json.dump({"enabled": True,
                           "targets": [{"name": "db", "type": "sqlite",
                                        "backup_dir": bdir, "glob": "*.ok"}]}, fh)
            self.assertEqual(rt.main(["--config", cfg]), 1)


if __name__ == "__main__":
    unittest.main()
