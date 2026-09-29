#!/usr/bin/env python3
"""Tests for scripts/budget_guard.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import budget_guard as bg  # noqa: E402


def _files(tmp, config, usage):
    cfg = os.path.join(tmp, "cfg.json")
    usg = os.path.join(tmp, "usg.json")
    with open(cfg, "w") as fh:
        json.dump(config, fh)
    with open(usg, "w") as fh:
        json.dump(usage, fh)
    return cfg, usg


class BudgetGuardTest(unittest.TestCase):
    def test_disabled_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, usg = _files(tmp, {"enabled": False}, {"spend": {"a": 999}})
            self.assertEqual(bg.main(["--config", cfg, "--usage", usg]), 0)

    def test_under_limit_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, usg = _files(tmp,
                {"enabled": True, "fleet_limit": 100, "default_agent_limit": 50},
                {"spend": {"a": 10, "b": 20}})
            self.assertEqual(bg.main(["--config", cfg, "--usage", usg]), 0)

    def test_agent_over_limit_exit1(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, usg = _files(tmp,
                {"enabled": True, "default_agent_limit": 5},
                {"spend": {"a": 10}})
            self.assertEqual(bg.main(["--config", cfg, "--usage", usg]), 1)

    def test_fleet_over_limit_exit1(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, usg = _files(tmp,
                {"enabled": True, "fleet_limit": 15},
                {"spend": {"a": 10, "b": 10}})
            self.assertEqual(bg.main(["--config", cfg, "--usage", usg]), 1)

    def test_list_usage_form_and_status_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, usg = _files(tmp,
                {"enabled": True, "agent_limits": {"a": 5}},
                [{"agent": "a", "cost": 3}, {"agent": "a", "cost": 4}])
            sf = os.path.join(tmp, "status.json")
            rc = bg.main(["--config", cfg, "--usage", usg, "--status-file", sf])
            self.assertEqual(rc, 1)  # 3+4=7 > 5
            with open(sf) as fh:
                st = json.load(fh)
            self.assertTrue(st["breached"])


if __name__ == "__main__":
    unittest.main()
