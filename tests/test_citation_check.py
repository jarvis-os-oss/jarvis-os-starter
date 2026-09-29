#!/usr/bin/env python3
"""Tests for scripts/citation_check.py."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import citation_check as cc  # noqa: E402


class CitationCheckTest(unittest.TestCase):
    def test_fully_grounded(self):
        ans = "The sky appears blue due to scattering [1]. Water boils at 100 C [2]."
        src = {"1": "rayleigh scattering makes the sky appear blue",
               "2": "water boils at 100 degrees celsius at sea level"}
        r = cc.check(ans, src)
        self.assertTrue(r["grounded"])

    def test_ungrounded_sentence(self):
        ans = "This claim has a citation [1]. This other claim has none at all here."
        src = {"1": "supporting text"}
        r = cc.check(ans, src)
        self.assertFalse(r["grounded"])
        self.assertEqual(len(r["ungrounded_sentences"]), 1)

    def test_dangling_marker(self):
        ans = "A statement pointing at a missing source [9]."
        src = {"1": "something"}
        r = cc.check(ans, src)
        self.assertFalse(r["grounded"])
        self.assertEqual(r["dangling_markers"][0]["marker"], "9")

    def test_weak_overlap_flagged(self):
        ans = "Completely unrelated tokens alpha beta gamma delta epsilon [1]."
        src = {"1": "nothing shared whatsoever here totally different"}
        r = cc.check(ans, src, min_overlap=0.5)
        self.assertFalse(r["grounded"])
        self.assertTrue(r["weak_support"])

    def test_overlap_off_by_default(self):
        ans = "Unrelated content zeta eta theta [1]."
        src = {"1": "different words entirely"}
        r = cc.check(ans, src)
        self.assertTrue(r["grounded"])


if __name__ == "__main__":
    unittest.main()
