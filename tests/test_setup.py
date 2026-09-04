"""Tests for scripts/setup.py: non-interactive run produces a valid .env."""

import os
import subprocess
import sys
import tempfile
import shutil
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SetupTest(unittest.TestCase):
    def setUp(self):
        # Work on a throwaway copy so we never touch the real repo .env / roster.
        self.tmp = tempfile.mkdtemp(prefix="aios-setup-")
        for rel in [".env.example", "scripts", "dashboard"]:
            src = os.path.join(ROOT, rel)
            dst = os.path.join(self.tmp, rel)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        # a fake .git dir so wire_upstream has something, but skip remote ops
        os.makedirs(os.path.join(self.tmp, ".git"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_non_interactive_generates_env(self):
        env = dict(os.environ)
        env["COCKPIT_PUBLIC_DOMAIN"] = "cockpit.test"
        r = subprocess.run(
            [sys.executable, os.path.join(self.tmp, "scripts", "setup.py"),
             "--non-interactive", "--skip-upstream", "--skip-rename", "--force"],
            capture_output=True, text=True, env=env, cwd=self.tmp,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        env_path = os.path.join(self.tmp, ".env")
        self.assertTrue(os.path.exists(env_path), "setup did not write .env")
        with open(env_path) as fh:
            content = fh.read()
        # Required keys present.
        for key in ["COCKPIT_TOKEN=", "API_SERVER_KEY=", "AIOS_INSTANCE_NAME=", "COCKPIT_PORT="]:
            self.assertIn(key, content)
        # Secrets were auto-generated, not left as the placeholder.
        self.assertNotIn("COCKPIT_TOKEN=change-me-to-a-long-random-token", content)
        self.assertNotIn("API_SERVER_KEY=change-me-agent-server-key", content)
        # File permissions locked down.
        self.assertEqual(oct(os.stat(env_path).st_mode)[-3:], "600")


if __name__ == "__main__":
    unittest.main()
