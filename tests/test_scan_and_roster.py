"""Tests for the secret / PII scanner and cockpit roster integrity."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANNER = os.path.join(ROOT, "scripts", "scan_secrets.py")


class ScanSecretsTest(unittest.TestCase):
    def test_repo_is_clean(self):
        r = subprocess.run(
            [sys.executable, SCANNER], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0, f"scanner flagged the repo:\n{r.stdout}")

    def test_scanner_catches_a_planted_secret(self):
        # Plant a fake secret in a temp file inside the tree, scan --all, expect fail.
        planted = os.path.join(ROOT, "tests", "_planted_tmp.txt")
        try:
            with open(planted, "w") as fh:
                fh.write("token AKIA" + "ABCDEFGHIJKLMNOP\n")
            r = subprocess.run(
                [sys.executable, SCANNER, "--all"], capture_output=True, text=True
            )
            self.assertEqual(r.returncode, 1, "scanner missed a planted AWS-style key")
            self.assertIn("AWS access key", r.stdout)
        finally:
            os.remove(planted)

    def test_scanner_catches_denylisted_token(self):
        planted = os.path.join(ROOT, "tests", "_planted_pii.txt")
        # Build the denylisted token from parts so this literal never sits in a
        # tracked file (which would make the scanner flag its own test).
        token = "bracket" + "lab"
        try:
            with open(planted, "w") as fh:
                fh.write(f"some reference to {token} here\n")
            r = subprocess.run(
                [sys.executable, SCANNER, "--all"], capture_output=True, text=True
            )
            self.assertEqual(r.returncode, 1, "scanner missed a denylisted token")
            self.assertIn("DENYLISTED", r.stdout)
        finally:
            os.remove(planted)


class RosterTest(unittest.TestCase):
    def test_roster_valid_and_has_jarvis(self):
        with open(os.path.join(ROOT, "dashboard", "team_config.json")) as fh:
            data = json.load(fh)
        agents = data.get("agents", [])
        self.assertGreaterEqual(len(agents), 6)
        keys = {a["key"] for a in agents}
        self.assertIn("default", keys)  # JARVIS
        # Every agent has the fields the cockpit renders.
        for a in agents:
            for field in ("key", "name", "role", "desc"):
                self.assertIn(field, a)

    def test_every_agent_has_a_soul_file(self):
        with open(os.path.join(ROOT, "dashboard", "team_config.json")) as fh:
            data = json.load(fh)
        for a in data["agents"]:
            key = "jarvis" if a["key"] == "default" else a["key"]
            path = os.path.join(ROOT, "agents", f"{key}.SOUL.md")
            self.assertTrue(os.path.exists(path), f"missing SOUL for {a['key']}: {path}")


if __name__ == "__main__":
    unittest.main()
