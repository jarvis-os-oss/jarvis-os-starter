"""Tests for the host-reboot grace in the restart-loop breaker reference patch.

Proves: (1) a fast legitimate host-reboot cascade (low uptime) never trips the breaker and
resets the chain; (2) a real crash loop on a long-running host (high uptime) is still capped;
(3) unreadable uptime fails CLOSED; (4) the grace can be disabled; (5) helper boundaries.

Self-contained: loads the shipped reference file directly (no runtime install needed) and stubs
the runtime constants module onto a temp home.
"""
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD_SRC = Path(ROOT) / "gateway-fixes" / "loopbreaker-reboot-grace" / "restart_loop_guard.patched.py"


def _load_guard(tmp_home):
    stub = types.ModuleType("hermes_constants")
    stub.get_hermes_home = lambda: tmp_home
    sys.modules["hermes_constants"] = stub
    sys.modules.pop("restart_loop_guard_under_test", None)
    spec = importlib.util.spec_from_file_location("restart_loop_guard_under_test", GUARD_SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["restart_loop_guard_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class RebootGraceTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.home = Path(self._td.name)
        (self.home / "gateway").mkdir(parents=True, exist_ok=True)
        self._saved = sys.modules.get("hermes_constants")

    def tearDown(self):
        sys.modules.pop("restart_loop_guard_under_test", None)
        if self._saved is None:
            sys.modules.pop("hermes_constants", None)
        else:
            sys.modules["hermes_constants"] = self._saved
        self._td.cleanup()

    def test_real_reboot_cascade_never_trips(self):
        g = _load_guard(self.home)
        g.clear()
        t = 1000.0
        g._save_boots([t - 200, t - 100, t - 5])
        for i, up in enumerate((5.0, 10.0, 15.0)):
            boots = g.record_restart_interrupted_boot(now=t + i, reboot_grace_seconds=120, uptime=up)
            self.assertEqual(boots, [t + i])

    def test_crash_loop_high_uptime_still_caps(self):
        g = _load_guard(self.home)
        g.clear()
        t = 2000.0
        results = []
        for i in range(3):
            boots = g.record_restart_interrupted_boot(
                now=t + i * 10, reboot_grace_seconds=120, uptime=5000.0)
            results.append(len(boots))
        self.assertEqual(results, [1, 2, 3])
        g._system_uptime_seconds = lambda: 5000.0
        self.assertTrue(g.check_and_record(max_restarts=3, now=t + 30, reboot_grace_seconds=120))

    def test_unreadable_uptime_fails_closed(self):
        g = _load_guard(self.home)
        g.clear()
        t = 3000.0
        g._system_uptime_seconds = lambda: None
        results = [len(g.record_restart_interrupted_boot(now=t + i * 10, reboot_grace_seconds=120))
                   for i in range(3)]
        self.assertEqual(results, [1, 2, 3])

    def test_grace_disabled(self):
        g = _load_guard(self.home)
        g.clear()
        t = 4000.0
        results = [len(g.record_restart_interrupted_boot(
            now=t + i * 10, reboot_grace_seconds=0, uptime=5.0)) for i in range(3)]
        self.assertEqual(results, [1, 2, 3])

    def test_helper_boundaries(self):
        g = _load_guard(self.home)
        self.assertIs(g._is_host_reboot_boot(120, uptime=119.9), True)
        self.assertIs(g._is_host_reboot_boot(120, uptime=120.0), False)
        self.assertIs(g._is_host_reboot_boot(0, uptime=5.0), False)
        # uptime=None means "read /proc/uptime": stub it so the result does not depend on the host
        g._system_uptime_seconds = lambda: None
        self.assertIs(g._is_host_reboot_boot(120), False)  # unreadable uptime fails closed
        g._system_uptime_seconds = lambda: 5.0
        self.assertIs(g._is_host_reboot_boot(120), True)

    def test_patch_reproduces_reference(self):
        """The shipped patch is present and touches only the guard file."""
        patch = (GUARD_SRC.parent / "restart_loop_guard.reboot-grace.patch").read_text(encoding="utf-8")
        self.assertIn("a/gateway/restart_loop_guard.py", patch)
        self.assertEqual(patch.count("diff --git"), 1)


if __name__ == "__main__":
    unittest.main()
