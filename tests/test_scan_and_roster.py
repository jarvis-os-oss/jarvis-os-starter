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
        # Use a GENERIC placeholder that ships in the default denylist, built
        # from parts so this literal never sits in a tracked file (which would
        # make the scanner flag its own test).
        token = "example" + "-corp"
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

    def test_structural_pass_flags_public_ip_even_in_scanner(self):
        # The self-exclude blind spot: layer 2 must flag a routable public IP
        # regardless of the denylist and WITHOUT exempting any file. The IP is
        # assembled at runtime so no contiguous public IP sits in this source.
        planted = os.path.join(ROOT, "tests", "_planted_ip.txt")
        pub = ".".join(["8", "8", "8", "8"])
        try:
            with open(planted, "w") as fh:
                fh.write(f"host {pub} reachable\n")
            r = subprocess.run(
                [sys.executable, SCANNER, "--all"], capture_output=True, text=True
            )
            self.assertEqual(r.returncode, 1, "scanner missed a routable public IP")
            self.assertIn("Routable public IP", r.stdout)
        finally:
            os.remove(planted)

    def test_rfc5737_and_private_ips_are_not_flagged(self):
        # Documentation ranges and private/loopback IPs are legitimate
        # placeholders and must NOT trip the scanner.
        planted = os.path.join(ROOT, "tests", "_planted_safe_ip.txt")
        try:
            with open(planted, "w") as fh:
                fh.write("doc 203.0.113.1 priv 10.0.0.5 lo 127.0.0.1 lan 192.168.1.1\n")
            r = subprocess.run(
                [sys.executable, SCANNER, "--all"], capture_output=True, text=True
            )
            self.assertEqual(
                r.returncode, 0,
                f"scanner wrongly flagged a safe/documentation IP:\n{r.stdout}",
            )
        finally:
            os.remove(planted)

    def test_scanner_source_has_no_real_denylist_terms(self):
        # The committed scanner must ship only generic placeholders, no real
        # owner names/IPs. These are neutral, fictional stand-ins that represent
        # the SHAPE of owner-specific terms (company, product, surname, infra
        # IP); each instance's real terms live only in the git-ignored
        # .scan_denylist.local and must never appear in this tracked scanner.
        with open(SCANNER, "r") as fh:
            src = fh.read().lower()
        real_terms = ["contoso", "fabri" + "kam", "mustermann"]
        # A private-range canary IP (RFC1918): stands in for a real infra IP
        # without itself being a routable public address.
        real_terms.append(".".join(["10", "11", "12", "13"]))
        for real in real_terms:
            self.assertNotIn(real, src, f"real term leaked into scanner: {real}")


class RosterTest(unittest.TestCase):
    def test_roster_valid_and_has_jarvis(self):
        with open(os.path.join(ROOT, "dashboard", "team_config.json")) as fh:
            data = json.load(fh)
        agents = data.get("agents", [])
        self.assertGreaterEqual(len(agents), 6)
        keys = {a["key"] for a in agents}
        self.assertIn("default", keys)  # the orchestrator
        # Every agent has the fields the cockpit renders.
        for a in agents:
            for field in ("key", "name", "role", "desc"):
                self.assertIn(field, a)

    def test_every_agent_has_a_soul_file(self):
        with open(os.path.join(ROOT, "dashboard", "team_config.json")) as fh:
            data = json.load(fh)
        for a in data["agents"]:
            # The roster maps each profile key to its persona via the "soul"
            # field (falls back to the key). default -> orchestrator.SOUL.md.
            soul = a.get("soul") or a["key"]
            path = os.path.join(ROOT, "agents", f"{soul}.SOUL.md")
            self.assertTrue(os.path.exists(path), f"missing SOUL for {a['key']}: {path}")


if __name__ == "__main__":
    unittest.main()
