#!/usr/bin/env python3
"""Tests for scripts/pr_security_audit.py. Secret-shaped test tokens are
assembled at runtime to avoid tripping the repo secret-scanner."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import pr_security_audit as pa  # noqa: E402


def _diff(body_lines, path="scripts/x.py"):
    header = [f"--- a/{path}", f"+++ b/{path}", "@@ -1,1 +1,%d @@" % len(body_lines)]
    return "\n".join(header + body_lines) + "\n"


class PrSecurityAuditTest(unittest.TestCase):
    def test_clean_diff(self):
        r = pa.audit(_diff(["+x = 1", "+y = 2"]))
        self.assertFalse(r["has_high"])

    def test_eval_flagged_high(self):
        r = pa.audit(_diff(["+result = eval(user_input)"]))
        self.assertTrue(r["has_high"])
        self.assertTrue(any(f["rule"] == "exec.eval" for f in r["findings"]))

    def test_shell_true_flagged(self):
        r = pa.audit(_diff(["+subprocess.run(cmd, shell=True)"]))
        self.assertTrue(any(f["rule"] == "exec.shell_true" for f in r["findings"]))

    def test_tls_disabled_flagged(self):
        r = pa.audit(_diff(["+requests.get(url, verify=False)"]))
        self.assertTrue(any(f["rule"] == "net.tls_disabled" for f in r["findings"]))

    def test_only_added_lines_scanned(self):
        # a removed line containing eval must NOT be flagged
        diff = _diff(["-old = eval(x)", "+new = safe(x)"])
        r = pa.audit(diff)
        self.assertFalse(r["has_high"])

    def test_line_numbers_tracked(self):
        diff = _diff(["+a = 1", "+b = 2", "+c = eval(z)"])
        f = [x for x in pa.audit(diff)["findings"] if x["rule"] == "exec.eval"][0]
        self.assertEqual(f["line"], 3)

    def test_secret_token_in_added_line(self):
        fake = "ghp_" + "d" * 36
        r = pa.audit(_diff([f"+TOKEN = '{fake}'"]))
        self.assertTrue(r["has_high"])


if __name__ == "__main__":
    unittest.main()
