#!/usr/bin/env python3
"""Tests for scripts/dependency_audit.py."""
from __future__ import annotations

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dependency_audit as da  # noqa: E402


class DependencyAuditTest(unittest.TestCase):
    def test_pinned_requirement_clean(self):
        r = da.audit("requirements.txt", "flask==2.3.0\nrequests==2.31.0\n")
        self.assertFalse(r["has_high"])
        self.assertEqual(r["medium"], 0)

    def test_unpinned_is_medium(self):
        r = da.audit("requirements.txt", "flask>=2.0\nrequests\n")
        self.assertEqual(r["high"], 0)
        self.assertEqual(r["medium"], 2)

    def test_vcs_source_is_high(self):
        r = da.audit("requirements.txt", "git+https://host/x/y.git#egg=y\n")
        self.assertTrue(r["has_high"])

    def test_package_json_install_hook_high(self):
        pkg = json.dumps({
            "dependencies": {"left-pad": "1.3.0"},
            "scripts": {"postinstall": "node evil.js"},
        })
        r = da.audit("package.json", pkg)
        self.assertTrue(r["has_high"])
        self.assertTrue(any(f["rule"] if "rule" in f else f["reason"] for f in r["findings"]))

    def test_package_json_pinned_clean(self):
        pkg = json.dumps({"dependencies": {"a": "1.0.0", "b": "2.5.1"}})
        r = da.audit("package.json", pkg)
        self.assertFalse(r["has_high"])
        self.assertEqual(r["medium"], 0)


if __name__ == "__main__":
    unittest.main()
