#!/usr/bin/env python3
"""Tests for scripts/skill_audit.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import skill_audit as sa  # noqa: E402


def _skill(root, name, desc="", body_lines=10):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    text = f"---\nname: {name}\ndescription: {desc}\n---\n" + "\n".join(
        f"line {i}" for i in range(body_lines))
    with open(os.path.join(d, "SKILL.md"), "w") as fh:
        fh.write(text)
    return os.path.join(d, "SKILL.md")


class SkillAuditTest(unittest.TestCase):
    def test_clean_library_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            _skill(tmp, "alpha", "does alpha things clearly")
            _skill(tmp, "beta", "handles beta stuff distinctly")
            skills = sa._find_skills(tmp)
            findings = sa.audit(skills, max_lines=500, stale_days=0,
                                desc_threshold=0.85)
            self.assertEqual(findings, [])

    def test_oversize_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _skill(tmp, "big", "a big skill", body_lines=600)
            skills = sa._find_skills(tmp)
            findings = sa.audit(skills, max_lines=100, stale_days=0,
                                desc_threshold=0.85)
            self.assertTrue(any(f["type"] == "OVERSIZE" for f in findings))

    def test_no_desc_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _skill(tmp, "nodesc", "")
            skills = sa._find_skills(tmp)
            findings = sa.audit(skills, max_lines=500, stale_days=0,
                                desc_threshold=0.85)
            self.assertTrue(any(f["type"] == "NO_DESC" for f in findings))

    def test_dup_desc_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _skill(tmp, "one", "monitor the system for anomalies and alert")
            _skill(tmp, "two", "monitor the system for anomalies and alert")
            skills = sa._find_skills(tmp)
            findings = sa.audit(skills, max_lines=500, stale_days=0,
                                desc_threshold=0.85)
            self.assertTrue(any(f["type"] == "DUP_DESC" for f in findings))

    def test_main_exit1_on_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            _skill(tmp, "nodesc", "")
            self.assertEqual(sa.main([tmp, "--format", "json"]), 1)

    def test_main_bad_dir_exit2(self):
        self.assertEqual(sa.main(["/nonexistent/xyz"]), 2)


if __name__ == "__main__":
    unittest.main()
