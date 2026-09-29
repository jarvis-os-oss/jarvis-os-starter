#!/usr/bin/env python3
"""Tests for scripts/style_lint.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import style_lint as sl  # noqa: E402

EMDASH = "\u2014"


def _cfg(tmp, config):
    p = os.path.join(tmp, "cfg.json")
    with open(p, "w") as fh:
        json.dump(config, fh)
    return p


class StyleLintTest(unittest.TestCase):
    def test_disabled_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "a.md")
            with open(f, "w") as fh:
                fh.write(f"bad {EMDASH} dash")
            cfg = _cfg(tmp, {"enabled": False, "rules": [
                {"id": "d", "type": "substring", "pattern": EMDASH}]})
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp, f]), 0)

    def test_substring_violation_exit1(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "a.md")
            with open(f, "w") as fh:
                fh.write(f"bad {EMDASH} dash")
            cfg = _cfg(tmp, {"enabled": True, "rules": [
                {"id": "d", "type": "substring", "pattern": EMDASH,
                 "message": "no dash"}]})
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp, f]), 1)

    def test_clean_file_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "a.md")
            with open(f, "w") as fh:
                fh.write("clean hyphen - only")
            cfg = _cfg(tmp, {"enabled": True, "rules": [
                {"id": "d", "type": "regex", "pattern": "[\u2014\u2013]"}]})
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp, f]), 0)

    def test_regex_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "a.txt")
            with open(f, "w") as fh:
                fh.write("TODO: fix this")
            cfg = _cfg(tmp, {"enabled": True, "rules": [
                {"id": "todo", "type": "regex", "pattern": "TODO",
                 "message": "no TODO"}]})
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp, f]), 1)

    def test_glob_discovery_when_no_files_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "a.md"), "w") as fh:
                fh.write(f"x {EMDASH}")
            with open(os.path.join(tmp, "b.py"), "w") as fh:
                fh.write(f"y {EMDASH}")  # excluded by include_globs
            cfg = _cfg(tmp, {"enabled": True, "include_globs": ["**/*.md"],
                             "rules": [{"id": "d", "type": "substring",
                                        "pattern": EMDASH}]})
            # only a.md scanned -> 1 hit -> exit 1
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp]), 1)

    def test_ignore_case_substring(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "a.md")
            with open(f, "w") as fh:
                fh.write("Forbidden WORD here")
            cfg = _cfg(tmp, {"enabled": True, "rules": [
                {"id": "w", "type": "substring", "pattern": "word",
                 "ignore_case": True}]})
            self.assertEqual(sl.main(["--config", cfg, "--root", tmp, f]), 1)


if __name__ == "__main__":
    unittest.main()
