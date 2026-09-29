#!/usr/bin/env python3
"""Tests for scripts/price_monitor.py. Real temp files, no network."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import price_monitor as pm  # noqa: E402


class PriceMonitorTest(unittest.TestCase):
    def test_target_reached_alerts(self):
        cfg = {"enabled": True, "items": [{"name": "widget", "target_price": 20.0}]}
        alerts, state = pm.evaluate(cfg, {"widget": 15.0})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["name"], "widget")
        self.assertIn("widget", state)

    def test_target_not_reached(self):
        cfg = {"enabled": True, "items": [{"name": "widget", "target_price": 20.0}]}
        alerts, _ = pm.evaluate(cfg, {"widget": 25.0})
        self.assertEqual(alerts, [])

    def test_history_accumulates_and_caps(self):
        cfg = {"enabled": True, "items": [{"name": "w", "target_price": 1.0}]}
        state = {}
        for i in range(60):
            _, state = pm.evaluate(cfg, {"w": 100.0 + i}, state)
        self.assertLessEqual(len(state["w"]["history"]), 50)

    def test_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            sp = os.path.join(tmp, "state.json")
            pm._save_state(sp, {"w": {"last_price": 9.0, "history": []}})
            loaded = pm._load_state(sp)
            self.assertEqual(loaded["w"]["last_price"], 9.0)

    def test_disabled_is_noop_via_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfgp = os.path.join(tmp, "cfg.json")
            with open(cfgp, "w") as fh:
                fh.write('{"enabled": false, "items": []}')
            rc = pm.main(["--config", cfgp, "--item", "w", "--price", "1.0"])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
