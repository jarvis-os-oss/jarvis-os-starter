"""Tests for the read-only upstream update-check surface.

The kit ships an opt-in, read-only way for an operator to learn that a newer
upstream state exists (scripts/check_upstream_updates.sh + a watchdog hook +
docs). These tests assert the safety contract holds: the checker only fetches
and reports, the watchdog hook is off by default, and the docs explain it. A
future edit that turns any of this into an auto-pull would break a test.
"""

import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class UpdateCheckScriptTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(ROOT, "scripts", "check_upstream_updates.sh")
        self.text = _read("scripts", "check_upstream_updates.sh")

    def test_exists_and_executable(self):
        self.assertTrue(os.path.exists(self.path))
        self.assertTrue(os.access(self.path, os.X_OK), "checker must be executable")

    def test_is_read_only_no_mutating_git(self):
        # It may fetch, but must never RUN pull/merge/reset/checkout/rebase.
        # Check command positions only: drop comment lines and the contents of
        # quoted strings (log/message text may name the manual `git merge`
        # step as operator guidance without executing it).
        self.assertIn("git fetch", self.text)
        code_lines = [
            ln for ln in self.text.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        code = "\n".join(code_lines)
        # remove double- and single-quoted spans
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        for forbidden in ("git merge", "git pull", "git reset ", "git checkout",
                          "git rebase"):
            self.assertNotIn(forbidden, code,
                             f"update checker must not run: {forbidden}")

    def test_valid_bash_syntax(self):
        r = subprocess.run(["bash", "-n", self.path], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_reports_behind_count_and_release(self):
        self.assertIn("rev-list --count", self.text)
        self.assertIn("tag", self.text)


class WatchdogHookTest(unittest.TestCase):
    def setUp(self):
        self.text = _read("infra", "watchdog.sh")

    def test_update_check_is_opt_in_and_defaults_off(self):
        # Default must be 0 (off); only AIOS_UPDATE_CHECK=1 activates it.
        self.assertIn("AIOS_UPDATE_CHECK", self.text)
        self.assertTrue(
            re.search(r'AIOS_UPDATE_CHECK:?=0', self.text)
            or ': "${AIOS_UPDATE_CHECK:=0}"' in self.text,
            "update check must default to off",
        )

    def test_hook_calls_the_checker(self):
        self.assertIn("check_upstream_updates.sh", self.text)


class UpstreamDocsTest(unittest.TestCase):
    def setUp(self):
        self.text = _read("docs", "UPSTREAM_UPDATES.md")

    def test_documents_releases_and_readonly_check(self):
        self.assertIn("check_upstream_updates.sh", self.text)
        self.assertIn("AIOS_UPDATE_CHECK", self.text)
        self.assertIn("Releases", self.text)

    def test_documents_portable_trailer_mechanism(self):
        self.assertIn("Portable: yes", self.text)
        self.assertIn("scan_secrets.py", self.text)
        self.assertIn("never auto-merged", self.text)


if __name__ == "__main__":
    unittest.main()
