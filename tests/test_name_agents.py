"""Tests for the agent naming step (scripts/name_agents.py).

Pure standard library. Runs the applier on a throwaway COPY of the repo so the
real tree is never mutated, and verifies:
  - the kit SHIPS every core persona with an unresolved {{AGENT_NAME}}
    placeholder (so the naming step is meaningful and no proper name is preset),
  - applying role defaults resolves every placeholder and --check passes,
  - a custom name lands in both the persona heading and the roster,
  - the applier is idempotent (a second run reports no change),
  - no core persona ships a preset internal proper name.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_SOULS = ["orchestrator", "assistant", "researcher", "developer",
              "maintenance", "writer"]
PLACEHOLDER = "{{AGENT_NAME}}"


def _run(repo, *args):
    return subprocess.run(
        [sys.executable, os.path.join(repo, "scripts", "name_agents.py"), *args],
        capture_output=True, text=True)


class NamingStepTest(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.repo, ignore_errors=True))
        for sub in ("agents", "scripts", "dashboard"):
            shutil.copytree(os.path.join(ROOT, sub),
                            os.path.join(self.repo, sub))

    def _soul(self, role):
        return os.path.join(self.repo, "agents", f"{role}.SOUL.md")

    def _roster(self):
        with open(os.path.join(self.repo, "dashboard", "team_config.json")) as fh:
            return json.load(fh)

    def test_kit_ships_placeholder_in_every_core_soul(self):
        # The SHIPPED persona files (as copied from the repo) must still carry
        # the placeholder, i.e. no proper name is baked in.
        for role in CORE_SOULS:
            with open(self._soul(role)) as fh:
                self.assertIn(PLACEHOLDER, fh.read(),
                              f"{role}.SOUL.md must ship with {PLACEHOLDER}")

    def test_check_fails_before_apply(self):
        r = _run(self.repo, "--check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_defaults_resolve_all_placeholders(self):
        r = _run(self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for role in CORE_SOULS:
            with open(self._soul(role)) as fh:
                self.assertNotIn(PLACEHOLDER, fh.read())
        self.assertEqual(_run(self.repo, "--check").returncode, 0)

    def test_custom_name_lands_in_soul_and_roster(self):
        names = os.path.join(self.repo, "agents", "names.local")
        with open(names, "w") as fh:
            fh.write("default = Athena\ndeveloper = Ada\n")
        r = _run(self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self._soul("orchestrator")) as fh:
            head = fh.readline()
        self.assertIn("Athena", head)
        roster = {a["key"]: a["name"] for a in self._roster()["agents"]}
        self.assertEqual(roster["default"], "Athena")
        self.assertEqual(roster["developer"], "Ada")

    def test_idempotent_second_run(self):
        _run(self.repo)
        r2 = _run(self.repo)
        self.assertEqual(r2.returncode, 0)
        self.assertIn("unchanged", r2.stdout)

    def test_no_core_soul_ships_a_preset_proper_name(self):
        # Heading must be the placeholder, not a real internal name.
        banned = re.compile(r"\b(jarvis|ada|scotty|donna|pen|scout|pixel)\b",
                            re.IGNORECASE)
        for role in CORE_SOULS:
            with open(self._soul(role)) as fh:
                head = fh.readline()
            self.assertNotRegex(head, banned,
                                f"{role}.SOUL.md heading has a preset name")


if __name__ == "__main__":
    unittest.main()
