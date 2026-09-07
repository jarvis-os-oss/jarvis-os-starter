"""Structure tests for the onboarding and go-live documentation.

These docs are part of the kit's onboarding surface: a going-live safety
checklist, an agent-onboarding interview prompt, a soul-length discipline note,
and a `hermes doctor` first-diagnostic pointer. The tests assert the files exist
and carry the load-bearing content, so a future edit cannot silently gut them.
"""

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class GoingLiveDocTest(unittest.TestCase):
    def setUp(self):
        self.text = _read("docs", "GOING_LIVE.md")

    def test_covers_the_five_checks(self):
        for needle in (
            "TELEGRAM_ALLOWED_USERS",
            "scan_secrets.py",
            "127.0.0.1",
            "without explicit approval",
            "gateway stop",
        ):
            self.assertIn(needle, self.text, f"go-live checklist missing: {needle}")

    def test_points_at_hermes_doctor(self):
        self.assertIn("hermes doctor", self.text)


class OnboardingInterviewDocTest(unittest.TestCase):
    def setUp(self):
        self.text = _read("agents", "ONBOARDING_INTERVIEW.md")

    def test_is_an_interview_prompt(self):
        # The defining trait: interview one question at a time, show before writing.
        self.assertIn("INTERVIEW", self.text)
        self.assertIn("ONE at a time", self.text)
        self.assertIn("SHOW them to me BEFORE writing", self.text)

    def test_keeps_the_never_without_approval_boundary(self):
        self.assertIn("explicit approval", self.text)

    def test_stays_multi_agent(self):
        # Must not drift into single-agent framing; it defines a sub-agent under JARVIS.
        self.assertIn("JARVIS", self.text)


class DocReferencesTest(unittest.TestCase):
    def test_readme_links_the_new_docs(self):
        readme = _read("README.md")
        self.assertIn("docs/GOING_LIVE.md", readme)
        self.assertIn("agents/ONBOARDING_INTERVIEW.md", readme)

    def test_agents_readme_has_soul_length_note(self):
        agents_readme = _read("agents", "README.md")
        self.assertIn("wc -c agents/*.SOUL.md", agents_readme)
        self.assertIn("every single turn", agents_readme)

    def test_hermes_install_has_doctor(self):
        self.assertIn("hermes doctor", _read("docs", "HERMES_INSTALL.md"))


if __name__ == "__main__":
    unittest.main()
