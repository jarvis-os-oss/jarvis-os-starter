#!/usr/bin/env python3
"""Tests for scripts/cron_collision_scan.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import cron_collision_scan as ccs  # noqa: E402


def _write_jobs(path: str, jobs) -> None:
    with open(path, "w") as fh:
        json.dump({"jobs": jobs}, fh)


class CronCollisionTest(unittest.TestCase):
    def test_no_collision_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "jobs.json")
            _write_jobs(j, [{"id": "a", "schedule": "0 6 * * *"},
                            {"id": "b", "schedule": "0 7 * * *"}])
            self.assertEqual(ccs.scan([j], max_per_minute=1), 0)

    def test_collision_exit1(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "jobs.json")
            _write_jobs(j, [{"id": "a", "schedule": "0 6 * * *"},
                            {"id": "b", "schedule": "0 6 * * *"}])
            self.assertEqual(ccs.scan([j], max_per_minute=1), 1)

    def test_disabled_jobs_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "jobs.json")
            _write_jobs(j, [{"id": "a", "schedule": "0 6 * * *"},
                            {"id": "b", "schedule": "0 6 * * *", "enabled": False}])
            self.assertEqual(ccs.scan([j], max_per_minute=1), 0)

    def test_list_form_and_cron_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "jobs.json")
            with open(j, "w") as fh:
                json.dump([{"name": "x", "cron": "*/5 * * * *"},
                           {"name": "y", "cron": "*/5 * * * *"}], fh)
            self.assertEqual(ccs.scan([j], max_per_minute=1), 1)

    def test_bad_json_exit2(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "jobs.json")
            with open(j, "w") as fh:
                fh.write("{ not json")
            self.assertEqual(ccs.scan([j], max_per_minute=1), 2)


if __name__ == "__main__":
    unittest.main()
