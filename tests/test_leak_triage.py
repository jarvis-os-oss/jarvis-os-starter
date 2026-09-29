#!/usr/bin/env python3
"""Tests for scripts/leak_triage.py. Test tokens are assembled at runtime so
the repo secret-scanner never sees a literal secret-shaped string."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import leak_triage as lt  # noqa: E402


class LeakTriageTest(unittest.TestCase):
    def test_clean_text_no_leak(self):
        r = lt.scan("just some ordinary prose without any secrets in it")
        self.assertFalse(r["leaked"])
        self.assertEqual(r["count"], 0)

    def test_aws_key_detected_and_redacted(self):
        fake = "AKIA" + "1234567890ABCDEF"  # 16 chars after prefix, not a real key
        r = lt.scan(f"config: aws_key={fake}")
        self.assertTrue(r["leaked"])
        self.assertEqual(r["findings"][0]["type"], "aws_access_key")
        # full token must NOT appear in the redacted output
        self.assertNotIn(fake, r["findings"][0]["redacted"])

    def test_github_pat_detected(self):
        fake = "ghp_" + "a" * 36
        r = lt.scan(f"token: {fake}")
        self.assertTrue(r["leaked"])
        self.assertEqual(r["findings"][0]["type"], "github_pat_classic")

    def test_general_steps_present_when_leaked(self):
        fake = "sk-" + "b" * 40
        r = lt.scan(fake)
        self.assertTrue(r["leaked"])
        self.assertTrue(r["general_steps"])

    def test_line_number_reported(self):
        fake = "ghp_" + "c" * 36
        r = lt.scan(f"line1\nline2\n{fake}\n")
        self.assertEqual(r["findings"][0]["line"], 3)


if __name__ == "__main__":
    unittest.main()
