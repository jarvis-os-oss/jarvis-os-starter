#!/usr/bin/env python3
"""Tests for scripts/fleet_cost_report.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fleet_cost_report as fcr  # noqa: E402


class FleetCostReportTest(unittest.TestCase):
    def test_aggregates_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "u.json")
            with open(p, "w") as fh:
                json.dump({"records": [
                    {"agent": "a", "cost": 1.5},
                    {"agent": "a", "cost": 2.5},
                    {"agent": "b", "cost": 4.0}]}, fh)
            rep = fcr.build_report([p], {})
            self.assertAlmostEqual(rep["fleet_total"], 8.0)
            top = rep["agents"][0]
            self.assertEqual(top["key"], "a")
            self.assertAlmostEqual(top["cost"], 4.0)

    def test_list_form_and_spend_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = os.path.join(tmp, "1.json")
            p2 = os.path.join(tmp, "2.json")
            with open(p1, "w") as fh:
                json.dump([{"name": "x", "estimated_cost": 2.0}], fh)
            with open(p2, "w") as fh:
                json.dump({"spend": {"x": 3.0}}, fh)
            rep = fcr.build_report([p1, p2], {})
            self.assertAlmostEqual(rep["fleet_total"], 5.0)

    def test_roster_name_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "u.json")
            with open(p, "w") as fh:
                json.dump({"spend": {"a": 1.0}}, fh)
            roster = os.path.join(tmp, "r.json")
            with open(roster, "w") as fh:
                json.dump([{"key": "a", "name": "Alpha"}], fh)
            names = fcr._roster_names(roster)
            rep = fcr.build_report([p], names)
            self.assertEqual(rep["agents"][0]["name"], "Alpha")

    def test_main_json_output_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "u.json")
            with open(p, "w") as fh:
                json.dump({"spend": {"a": 1.0}}, fh)
            self.assertEqual(fcr.main([p, "--format", "json", "--roster",
                                       os.path.join(tmp, "none.json")]), 0)

    def test_no_input_exit2(self):
        self.assertEqual(fcr.main(["/nonexistent/path/xyz.json"]), 2)


if __name__ == "__main__":
    unittest.main()
