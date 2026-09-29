#!/usr/bin/env python3
"""Tests for scripts/cache_hygiene.py. Real files, real mtimes."""
from __future__ import annotations

import json
import os
import sys
import time
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import cache_hygiene as ch  # noqa: E402


def _old_file(path: str, age_days: float) -> None:
    with open(path, "w") as fh:
        fh.write("x" * 1024)
    old = time.time() - age_days * 86400
    os.utime(path, (old, old))


class CacheHygieneTest(unittest.TestCase):
    def test_dry_run_never_deletes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "cache")
            os.makedirs(cache)
            f = os.path.join(cache, "old.tmp")
            _old_file(f, 30)
            cfg = {"enabled": True, "targets": [
                {"path": cache, "glob": "*.tmp", "min_age_days": 7}]}
            self.assertEqual(ch.run(cfg, apply=False), 0)
            self.assertTrue(os.path.isfile(f))  # still there

    def test_disabled_blocks_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "cache")
            os.makedirs(cache)
            f = os.path.join(cache, "old.tmp")
            _old_file(f, 30)
            cfg = {"enabled": False, "targets": [
                {"path": cache, "glob": "*.tmp", "min_age_days": 7}]}
            self.assertEqual(ch.run(cfg, apply=True), 0)
            self.assertTrue(os.path.isfile(f))  # disabled -> no delete

    def test_apply_deletes_only_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "cache")
            os.makedirs(cache)
            old = os.path.join(cache, "old.tmp")
            fresh = os.path.join(cache, "fresh.tmp")
            _old_file(old, 30)
            _old_file(fresh, 1)
            cfg = {"enabled": True, "targets": [
                {"path": cache, "glob": "*.tmp", "min_age_days": 7}]}
            self.assertEqual(ch.run(cfg, apply=True), 0)
            self.assertFalse(os.path.isfile(old))
            self.assertTrue(os.path.isfile(fresh))

    def test_glob_scopes_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "cache")
            os.makedirs(cache)
            keep = os.path.join(cache, "keep.log")
            drop = os.path.join(cache, "drop.tmp")
            _old_file(keep, 30)
            _old_file(drop, 30)
            cfg = {"enabled": True, "targets": [
                {"path": cache, "glob": "*.tmp", "min_age_days": 7}]}
            self.assertEqual(ch.run(cfg, apply=True), 0)
            self.assertTrue(os.path.isfile(keep))
            self.assertFalse(os.path.isfile(drop))


if __name__ == "__main__":
    unittest.main()
