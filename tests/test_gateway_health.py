#!/usr/bin/env python3
"""Tests for scripts/gateway_health.py. Real state files + real pid checks."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gateway_health as gh  # noqa: E402


def _write_state(home: str, key: str, state: str, pid) -> None:
    if key == "default":
        path = os.path.join(home, "gateway_state.json")
    else:
        d = os.path.join(home, "profiles", key)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "gateway_state.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"gateway_state": state, "pid": pid}, fh)


class GatewayHealthTest(unittest.TestCase):
    def test_running_with_live_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_state(tmp, "default", "running", os.getpid())
            r = gh.profile_status(tmp, "default")
            self.assertTrue(r["running"])

    def test_running_with_dead_pid_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_state(tmp, "worker", "running", 999999)
            r = gh.profile_status(tmp, "worker")
            self.assertFalse(r["running"])

    def test_missing_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = gh.profile_status(tmp, "ghost")
            self.assertFalse(r["running"])
            self.assertIn("kein gateway_state", r["detail"])

    def test_stopped_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_state(tmp, "default", "stopped", os.getpid())
            r = gh.profile_status(tmp, "default")
            self.assertFalse(r["running"])

    def test_check_command_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_state(tmp, "default", "running", os.getpid())
            self.assertEqual(
                gh.main(["--hermes-home", tmp, "--profiles", "default", "check"]), 0)
            _write_state(tmp, "default", "running", 999999)
            self.assertEqual(
                gh.main(["--hermes-home", tmp, "--profiles", "default", "check"]), 1)

    def test_roster_keys_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            roster = os.path.join(tmp, "team_config.json")
            with open(roster, "w") as fh:
                json.dump([{"key": "alpha"}, {"key": "beta"}], fh)
            keys = gh._roster_keys(roster)
            self.assertEqual(set(keys), {"alpha", "beta"})


if __name__ == "__main__":
    unittest.main()
