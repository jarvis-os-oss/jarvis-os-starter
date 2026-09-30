#!/usr/bin/env python3
"""Tests for scripts/memory_snapshot.py. Real temp files, no network."""
from __future__ import annotations

import os
import sys
import tarfile
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import memory_snapshot as ms  # noqa: E402


class MemorySnapshotTest(unittest.TestCase):
    def test_create_snapshot_packs_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "memory")
            os.makedirs(src)
            with open(os.path.join(src, "note.md"), "w") as fh:
                fh.write("remember this")
            dest = os.path.join(tmp, "snaps")
            out, present = ms.create_snapshot([src], dest)
            self.assertTrue(os.path.isfile(out))
            self.assertEqual(len(present), 1)
            with tarfile.open(out) as tar:
                names = tar.getnames()
            self.assertTrue(any("note.md" in n for n in names))

    def test_missing_source_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "snaps")
            out, present = ms.create_snapshot([os.path.join(tmp, "nope")], dest)
            self.assertTrue(os.path.isfile(out))
            self.assertEqual(present, [])

    def test_prune_removes_old_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.path.join(tmp, "memsnap-20200101T000000Z.tar.gz")
            new = os.path.join(tmp, "memsnap-20990101T000000Z.tar.gz")
            other = os.path.join(tmp, "unrelated.tar.gz")
            for p in (old, new, other):
                open(p, "w").close()
            past = time.time() - 40 * 86400
            os.utime(old, (past, past))
            removed = ms.prune(tmp, 30)
            self.assertIn(old, removed)
            self.assertTrue(os.path.isfile(new))
            self.assertTrue(os.path.isfile(other))  # non-snapshot untouched

    def test_disabled_is_noop_via_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfgp = os.path.join(tmp, "cfg.json")
            with open(cfgp, "w") as fh:
                fh.write('{"enabled": false, "sources": [], "dest": "x"}')
            self.assertEqual(ms.main(["--config", cfgp]), 0)

    def test_list_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "memsnap-20990101T000000Z.tar.gz"), "w").close()
            self.assertEqual(len(ms.list_snapshots(tmp)), 1)


if __name__ == "__main__":
    unittest.main()
