"""Unit tests for the tiered model-routing applier (model-routing/apply_routing.py).

Pure standard library (unittest). No network, no `hermes` CLI needed: every test
drives build_plan / run in dry-run mode and asserts on the emitted argv, so it
runs in CI on any machine.

Covers the safety-critical behaviour:
- only enabled agents are routed on --apply; the master flag gates everything;
- the main reasoning session (model.default) is NEVER touched;
- excluded_slots is enforced at runtime (routing an excluded slot raises);
- --revert resets routed slots to auto and reaches even disabled agents.
"""

import copy
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODROUTE = os.path.join(ROOT, "model-routing")
sys.path.insert(0, MODROUTE)

import apply_routing as ar  # noqa: E402

HERE = Path(MODROUTE)


class TestRoutingPlan(unittest.TestCase):
    def setUp(self):
        self.cfg = ar.load_config(HERE / "routing.json")

    @staticmethod
    def _on(cfg, name):
        # Reach an agent through build_plan's apply path (validation only runs
        # for enabled agents), so validation/guardrail tests actually trigger it.
        cfg["enabled"] = True
        cfg["agents"][name]["enabled"] = True
        return cfg

    def test_config_loads_and_shapes(self):
        self.assertIn("tiers", self.cfg)
        self.assertIn("cheap", self.cfg["tiers"])
        self.assertIn("main", self.cfg["tiers"])
        # Shipped disabled by default: an operator must opt in deliberately.
        self.assertFalse(self.cfg.get("enabled", False))

    def test_master_flag_off_blocks_apply(self):
        # As shipped (enabled=false) nothing is routed on apply.
        plan = ar.build_plan(self.cfg, only=None, revert=False)
        self.assertEqual(plan, [])

    def test_enabled_agents_are_routed_when_master_on(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["enabled"] = True
        cfg["agents"]["scout"]["enabled"] = True
        plan = ar.build_plan(cfg, only=None, revert=False)
        names = {name for name, _, _ in plan}
        self.assertIn("scout", names)

    def test_main_model_never_touched(self):
        # The whole point: the reasoning session stays on the frontier model.
        cfg = copy.deepcopy(self.cfg)
        cfg["enabled"] = True
        for a in cfg["agents"]:
            if not a.startswith("_"):
                cfg["agents"][a]["enabled"] = True
        for name, _, cmds in ar.build_plan(cfg, only=None, revert=False):
            flat = " ".join(" ".join(c) for c in cmds)
            self.assertNotIn("model.default", flat, name)
            self.assertNotIn("model.provider", flat, name)

    def test_scout_routes_expected_slots(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["enabled"] = True
        cfg["agents"]["scout"]["enabled"] = True
        plan = ar.build_plan(cfg, only="scout", revert=False)
        self.assertEqual(len(plan), 1)
        _, _, cmds = plan[0]
        flat = [" ".join(c) for c in cmds]
        cheap_model = cfg["tiers"]["cheap"]["model"]
        cheap_prov = cfg["tiers"]["cheap"]["provider"]
        for task in cfg["agents"]["scout"]["auxiliary_tasks"]:
            self.assertIn(f"hermes config set auxiliary.{task}.provider {cheap_prov}", flat)
            self.assertIn(f"hermes config set auxiliary.{task}.model {cheap_model}", flat)

    def test_excluded_approval_never_routed(self):
        # An agent that can trigger a side effect keeps 'approval' on the frontier
        # model: no cheap mis-score may ever auto-approve a real send/spend/book.
        cfg = copy.deepcopy(self.cfg)
        cfg["enabled"] = True
        cfg["agents"]["assistant"]["enabled"] = True
        plan = ar.build_plan(cfg, only="assistant", revert=False)
        _, _, cmds = plan[0]
        joined = " ".join(" ".join(c) for c in cmds)
        self.assertNotIn("auxiliary.approval.model", joined)
        self.assertNotIn("delegation.model", joined)
        self.assertEqual(
            set(cfg["agents"]["assistant"]["excluded_slots"]),
            {"approval", "delegation"})

    def test_excluded_slot_collision_is_rejected(self):
        # Enforced at runtime: slipping an excluded slot into auxiliary_tasks must
        # raise, not silently route the protected slot to the cheap tier.
        cfg = copy.deepcopy(self.cfg)
        cfg["agents"]["assistant"]["auxiliary_tasks"] = [
            "compression", "title_generation", "approval"]
        self._on(cfg, "assistant")
        with self.assertRaises(ValueError):
            ar.build_plan(cfg, only="assistant", revert=False)

    def test_excluded_delegation_conflict_is_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["agents"]["assistant"]["delegation"] = True
        self._on(cfg, "assistant")
        with self.assertRaises(ValueError):
            ar.build_plan(cfg, only="assistant", revert=False)

    def test_unknown_excluded_slot_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["agents"]["assistant"]["excluded_slots"] = ["not_a_slot"]
        self._on(cfg, "assistant")
        with self.assertRaises(ValueError):
            ar.build_plan(cfg, only="assistant", revert=False)

    def test_unknown_aux_task_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["agents"]["scout"]["auxiliary_tasks"] = ["not_a_real_task"]
        self._on(cfg, "scout")
        with self.assertRaises(ValueError):
            ar.build_plan(cfg, only="scout", revert=False)

    def test_missing_hermes_home_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        del cfg["agents"]["scout"]["hermes_home"]
        self._on(cfg, "scout")
        with self.assertRaises(ValueError):
            ar.build_plan(cfg, only="scout", revert=False)

    def test_revert_resets_to_auto_and_reaches_disabled(self):
        # revert ignores enabled flags so a disabled agent can still be cleaned up.
        plan = ar.build_plan(self.cfg, only="scout", revert=True)
        self.assertEqual(len(plan), 1)
        _, _, cmds = plan[0]
        flat = [" ".join(c) for c in cmds]
        for task in self.cfg["agents"]["scout"]["auxiliary_tasks"]:
            self.assertIn(f"hermes config set auxiliary.{task}.provider auto", flat)
        self.assertIn("hermes config unset delegation.model", flat)
        self.assertIn("hermes config unset delegation.provider", flat)

    def test_dry_run_returns_zero_and_runs_nothing(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["enabled"] = True
        cfg["agents"]["scout"]["enabled"] = True
        rc = ar.run(cfg, only="scout", revert=False, apply=False)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
