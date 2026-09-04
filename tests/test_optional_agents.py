"""Structure tests for the optional (Package 2) agent templates.

Each optional agent lives in ``agents/optional/<name>/`` and must ship a
``SOUL.md`` (persona) and a ``README.md`` (import guide). The SOUL must carry the
mandatory sections used across the kit, and the whole set must stay neutral (the
secret / PII scanner in tests/test_scan_and_roster.py enforces neutrality).
"""

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIONAL_DIR = os.path.join(ROOT, "agents", "optional")

# The nine specialised templates expected in Package 2.
EXPECTED_AGENTS = [
    "travel",
    "shopping",
    "style-advisor",
    "health-coach",
    "bookkeeping",
    "finance-advisor",
    "vehicle-manager",
    "marketing-leadgen",
    "design",
]

# Mandatory SOUL.md section headings (same convention as the base agents).
REQUIRED_SOUL_SECTIONS = [
    "## Role",
    "## Scope",
    "## Way of working",
    "## Collaboration",
    "## Escalation",
    "## Communication style",
    "## Hard rules",
]

# Every SOUL must restate these guardrails (present verbatim in all nine).
REQUIRED_HARD_RULES = [
    "em-dash",          # no em-dashes in output
    "spend money",      # never send / spend / book on your own
    "escalate",         # escalate when risky or ambiguous
    "credentials",      # never expose secrets / credentials
]

# Agents that must carry an explicit non-advice / non-clinical warning.
WARNING_REQUIRED = {
    "health-coach": "does NOT provide medical advice",
    "finance-advisor": "does NOT provide binding or regulated investment",
}


class OptionalAgentsStructureTest(unittest.TestCase):
    def test_all_expected_agents_present(self):
        present = sorted(
            d for d in os.listdir(OPTIONAL_DIR)
            if os.path.isdir(os.path.join(OPTIONAL_DIR, d))
        )
        self.assertEqual(present, sorted(EXPECTED_AGENTS),
                         f"optional agent folders differ: {present}")

    def test_each_agent_has_soul_and_readme(self):
        for name in EXPECTED_AGENTS:
            soul = os.path.join(OPTIONAL_DIR, name, "SOUL.md")
            readme = os.path.join(OPTIONAL_DIR, name, "README.md")
            self.assertTrue(os.path.isfile(soul), f"missing SOUL.md for {name}")
            self.assertTrue(os.path.isfile(readme), f"missing README.md for {name}")

    def test_soul_has_required_sections(self):
        for name in EXPECTED_AGENTS:
            with open(os.path.join(OPTIONAL_DIR, name, "SOUL.md")) as fh:
                text = fh.read()
            for section in REQUIRED_SOUL_SECTIONS:
                self.assertIn(section, text,
                              f"{name}/SOUL.md missing section '{section}'")

    def test_soul_restates_core_guardrails(self):
        for name in EXPECTED_AGENTS:
            with open(os.path.join(OPTIONAL_DIR, name, "SOUL.md")) as fh:
                text = fh.read().lower()
            for rule in REQUIRED_HARD_RULES:
                self.assertIn(rule.lower(), text,
                              f"{name}/SOUL.md missing guardrail '{rule}'")

    def test_soul_has_no_em_dash(self):
        # The kit-wide rule: no em-dashes anywhere in agent output/templates.
        for name in EXPECTED_AGENTS:
            with open(os.path.join(OPTIONAL_DIR, name, "SOUL.md")) as fh:
                text = fh.read()
            self.assertNotIn("\u2014", text, f"{name}/SOUL.md contains an em-dash")

    def test_advisory_agents_carry_explicit_warning(self):
        for name, needle in WARNING_REQUIRED.items():
            with open(os.path.join(OPTIONAL_DIR, name, "SOUL.md")) as fh:
                soul = fh.read()
            with open(os.path.join(OPTIONAL_DIR, name, "README.md")) as fh:
                readme = fh.read()
            self.assertIn(needle, soul,
                          f"{name}/SOUL.md missing required warning")
            self.assertIn(needle, readme,
                          f"{name}/README.md missing required warning")

    def test_readme_documents_import(self):
        for name in EXPECTED_AGENTS:
            with open(os.path.join(OPTIONAL_DIR, name, "README.md")) as fh:
                text = fh.read()
            # Must show the copy-into-agents step and a roster key.
            self.assertIn(f"agents/optional/{name}/SOUL.md", text,
                          f"{name}/README.md missing the import copy step")
            self.assertIn("team_config.json", text,
                          f"{name}/README.md missing the roster step")

    def test_overview_readme_lists_every_agent(self):
        with open(os.path.join(OPTIONAL_DIR, "README.md")) as fh:
            overview = fh.read()
        for name in EXPECTED_AGENTS:
            self.assertIn(name, overview,
                          f"agents/optional/README.md does not list {name}")


if __name__ == "__main__":
    unittest.main()
