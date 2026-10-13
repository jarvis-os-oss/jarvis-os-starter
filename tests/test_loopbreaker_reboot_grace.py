"""Tests fuer die Host-Reboot-Grace im Restart-Loop-Breaker (gateway-fixes/loopbreaker-reboot-grace).

Belegt: (1) eine schnelle Host-Reboot-Kaskade (niedrige Uptime) trippt den Breaker nie und
resettet die Kette; (2) ein Crash-Loop bei hoher Uptime wird weiter hart gekappt; (3) unlesbare
Uptime faellt closed; (4) die Grace ist mit reboot_grace_seconds<=0 abschaltbar; (5) Grenzwerte.

Laedt die mitgelieferte Referenz-Endversion direkt, hermes_constants wird gestubbt.
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


def load_guard(tmp_home):
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

    def tearDown(self):
        self._td.cleanup()
        sys.modules.pop("hermes_constants", None)

    def test_real_reboot_cascade_never_trips(self):
        g = load_guard(self.home)
        g.clear()
        t = 1000.0
        g._save_boots([t - 200, t - 100, t - 5])
        for i, up in enumerate((5.0, 10.0, 15.0)):
            boots = g.record_restart_interrupted_boot(now=t + i, reboot_grace_seconds=120, uptime=up)
            self.assertEqual(boots, [t + i])

    def test_crash_loop_high_uptime_still_caps(self):
        g = load_guard(self.home)
        g.clear()
        t = 2000.0
        results = []
        for i in range(3):
            boots = g.record_restart_interrupted_boot(now=t + i * 10, reboot_grace_seconds=120, uptime=5000.0)
            results.append(len(boots))
        self.assertEqual(results, [1, 2, 3])
        g._system_uptime_seconds = lambda: 5000.0
        self.assertTrue(g.check_and_record(max_restarts=3, now=t + 30, reboot_grace_seconds=120))

    def test_unreadable_uptime_fails_closed(self):
        g = load_guard(self.home)
        g.clear()
        g._system_uptime_seconds = lambda: None
        results = []
        for i in range(3):
            boots = g.record_restart_interrupted_boot(now=3000.0 + i * 10, reboot_grace_seconds=120)
            results.append(len(boots))
        self.assertEqual(results, [1, 2, 3])

    def test_grace_disabled(self):
        g = load_guard(self.home)
        g.clear()
        results = []
        for i in range(3):
            boots = g.record_restart_interrupted_boot(now=4000.0 + i * 10, reboot_grace_seconds=0, uptime=5.0)
            results.append(len(boots))
        self.assertEqual(results, [1, 2, 3])

    def test_helper_boundaries(self):
        g = load_guard(self.home)
        self.assertIs(g._is_host_reboot_boot(120, uptime=119.9), True)
        self.assertIs(g._is_host_reboot_boot(120, uptime=120.0), False)
        g._system_uptime_seconds = lambda: None
        self.assertIs(g._is_host_reboot_boot(120), False)
        self.assertIs(g._is_host_reboot_boot(0, uptime=5.0), False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
