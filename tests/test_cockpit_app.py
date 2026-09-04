"""Cockpit smoke test: boots the real Flask app and checks the token gate.

Skipped automatically if Flask is not installed (the CI job installs it). Uses
Flask's test client, no network sockets.
"""

import importlib
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard")

try:
    import flask  # noqa: F401
    HAVE_FLASK = True
except Exception:
    HAVE_FLASK = False


@unittest.skipUnless(HAVE_FLASK, "flask not installed")
class CockpitAppTest(unittest.TestCase):
    def setUp(self):
        os.environ["COCKPIT_TOKEN"] = "test-token-123"
        sys.path.insert(0, DASH)
        # Fresh import so the module picks up the token from the environment.
        for m in ("app", "cockpit_team"):
            if m in sys.modules:
                del sys.modules[m]
        self.appmod = importlib.import_module("app")
        self.client = self.appmod.app.test_client()

    def test_health_is_open(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_data_requires_token(self):
        self.assertEqual(self.client.get("/api/data").status_code, 401)
        r = self.client.get("/api/data?t=test-token-123")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.get_json()["agent_count"], 6)

    def test_team_requires_token_and_lists_agents(self):
        self.assertEqual(self.client.get("/api/team").status_code, 401)
        r = self.client.get("/api/team?t=test-token-123")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertGreaterEqual(data["count"], 6)
        keys = {a["key"] for a in data["agents"]}
        self.assertIn("default", keys)

    def test_index_denied_without_token(self):
        self.assertEqual(self.client.get("/").status_code, 401)

    def test_avatar_returns_svg(self):
        r = self.client.get("/avatar/default?t=test-token-123")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image/svg", r.headers.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main()
