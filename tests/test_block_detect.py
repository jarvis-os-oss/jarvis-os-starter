#!/usr/bin/env python3
"""Tests for scripts/block_detect.py."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import block_detect as bd  # noqa: E402


class BlockDetectTest(unittest.TestCase):
    def test_clean_200_not_blocked(self):
        r = bd.classify(200, {}, "<html><body>normal content here</body></html>")
        self.assertFalse(r["blocked"])
        self.assertEqual(r["kind"], "ok")

    def test_429_rate_limited_with_retry_after(self):
        r = bd.classify(429, {"Retry-After": "120"}, "")
        self.assertTrue(r["blocked"])
        self.assertEqual(r["kind"], "rate_limited")
        self.assertTrue(any("120" in x for x in r["reasons"]))
        self.assertTrue(r["recovery"])

    def test_403_forbidden(self):
        r = bd.classify(403, {}, "")
        self.assertTrue(r["blocked"])
        self.assertEqual(r["kind"], "forbidden")

    def test_soft_block_captcha_in_200_body(self):
        r = bd.classify(200, {}, "please solve this reCAPTCHA to continue")
        self.assertTrue(r["blocked"])
        self.assertEqual(r["kind"], "captcha")

    def test_paywall_body(self):
        r = bd.classify(200, {}, "Subscribe to continue reading this premium article")
        self.assertTrue(r["blocked"])

    def test_recovery_deduped(self):
        r = bd.classify(403, {}, "access denied by web application firewall bot detected")
        self.assertEqual(len(r["recovery"]), len(set(r["recovery"])))


if __name__ == "__main__":
    unittest.main()
