"""Unit tests for the cockpit file-first status resolution and collector.

Pure standard library (unittest + tempfiles); no Flask, no sockets, no network.
Covers the fix for the "all agents STOPPED" bug: the cockpit must trust a fresh
host-written status file, fall back to the TCP probe when the file is missing,
stale, or lacks a verdict, and the collector must derive liveness from each
profile's gateway_state.json plus a live pid.
"""

import importlib
import json
import os
import sys
import time
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard")
sys.path.insert(0, DASH)

cockpit_team = importlib.import_module("cockpit_team")
collect_status = importlib.import_module("collect_status")


class LoadStatusFileTest(unittest.TestCase):
    def _write(self, obj):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(obj, fh)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_fresh_file_is_used(self):
        path = self._write({"generated_at": time.time(),
                             "agents": {"scout": "running", "ada": "stopped"}})
        out = cockpit_team.load_status_file(path=path, max_age=180)
        self.assertEqual(out, {"scout": "running", "ada": "stopped"})

    def test_stale_file_is_rejected(self):
        path = self._write({"generated_at": time.time() - 10000,
                             "agents": {"scout": "running"}})
        self.assertEqual(cockpit_team.load_status_file(path=path, max_age=180), {})

    def test_missing_file_returns_empty(self):
        self.assertEqual(
            cockpit_team.load_status_file(path="/no/such/file.json"), {})

    def test_malformed_file_returns_empty(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            fh.write("{ not json")
        self.addCleanup(lambda: os.remove(path))
        self.assertEqual(cockpit_team.load_status_file(path=path), {})


class ResolveStatusTest(unittest.TestCase):
    def test_no_port_is_planned(self):
        self.assertEqual(
            cockpit_team.resolve_status({"key": "muse"}, {}), "planned")

    def test_file_verdict_wins_over_probe(self):
        # Port present but nothing listens; the file says running -> running.
        agent = {"key": "scout", "port": 8644}
        self.assertEqual(
            cockpit_team.resolve_status(agent, {"scout": "running"}), "running")

    def test_falls_back_to_probe_when_no_file_verdict(self):
        # No verdict in the map + a port that nothing listens on -> stopped
        # (the TCP probe refuses). Uses a high, almost-certainly-closed port.
        agent = {"key": "scout", "port": 65533}
        self.assertEqual(cockpit_team.resolve_status(agent, {}), "stopped")

    def test_ignores_garbage_verdict_and_probes(self):
        agent = {"key": "scout", "port": 65533}
        self.assertEqual(
            cockpit_team.resolve_status(agent, {"scout": "bogus"}), "stopped")


class CollectorStatusForTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.home,
                                                            ignore_errors=True))
        self._orig_home = collect_status.HERMES_HOME
        collect_status.HERMES_HOME = self.home
        self.addCleanup(setattr, collect_status, "HERMES_HOME", self._orig_home)

    def _write_state(self, key, obj):
        if key == "default":
            path = os.path.join(self.home, "gateway_state.json")
        else:
            d = os.path.join(self.home, "profiles", key)
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "gateway_state.json")
        with open(path, "w") as fh:
            json.dump(obj, fh)

    def test_planned_without_port(self):
        self.assertEqual(
            collect_status._status_for({"key": "muse"}), "planned")

    def test_stopped_when_state_file_missing(self):
        self.assertEqual(
            collect_status._status_for({"key": "ghost", "port": 8649}),
            "stopped")

    def test_running_requires_state_and_live_pid(self):
        # Our own pid is guaranteed alive.
        self._write_state("scout",
                          {"gateway_state": "running", "pid": os.getpid()})
        self.assertEqual(
            collect_status._status_for({"key": "scout", "port": 8644}),
            "running")

    def test_stopped_when_pid_dead(self):
        # A pid that cannot be alive.
        self._write_state("ada", {"gateway_state": "running", "pid": 2 ** 31 - 1})
        self.assertEqual(
            collect_status._status_for({"key": "ada", "port": 8645}),
            "stopped")

    def test_stopped_when_state_not_running(self):
        self._write_state("pen",
                          {"gateway_state": "stopped", "pid": os.getpid()})
        self.assertEqual(
            collect_status._status_for({"key": "pen", "port": 8655}),
            "stopped")


if __name__ == "__main__":
    unittest.main()
