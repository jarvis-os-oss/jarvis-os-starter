"""Cookie login: signed HttpOnly cookie after first login, fail closed."""

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

TOK = "test-token-123"
COOKIE = "cockpit_auth"


def _load(token=TOK):
    os.environ["COCKPIT_TOKEN"] = token
    sys.path.insert(0, DASH)
    for m in ("app", "cockpit_team"):
        sys.modules.pop(m, None)
    return importlib.import_module("app")


@unittest.skipUnless(HAVE_FLASK, "flask not installed")
class CookieLoginTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.client = self.mod.app.test_client()

    def test_token_login_sets_httponly_cookie_and_bare_url_works(self):
        self.assertEqual(self.client.get("/api/data").status_code, 401)
        r = self.client.get("/api/data?t=" + TOK)
        self.assertEqual(r.status_code, 200)
        sc = r.headers.get("Set-Cookie", "")
        self.assertIn(COOKIE + "=", sc)
        self.assertIn("HttpOnly", sc)
        self.assertNotIn(TOK, sc)
        self.assertEqual(self.client.get("/api/data").status_code, 200)

    def test_post_login(self):
        bad = self.client.post("/login", data={"t": "nope"})
        self.assertEqual(bad.status_code, 401)
        self.assertNotIn(COOKIE + "=", bad.headers.get("Set-Cookie", ""))
        ok = self.client.post("/login", data={"t": TOK})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(self.client.get("/api/data").status_code, 200)

    def test_forged_cookie_rejected(self):
        self.client.set_cookie(COOKIE, "forged.value.x")
        self.assertEqual(self.client.get("/api/data").status_code, 401)

    def test_cookie_survives_restart_and_dies_on_rotation(self):
        r = self.client.get("/api/data?t=" + TOK)
        raw = r.headers["Set-Cookie"].split(COOKIE + "=")[1].split(";")[0]
        again = _load().app.test_client()
        again.set_cookie(COOKIE, raw)
        self.assertEqual(again.get("/api/data").status_code, 200)
        rotated = _load("another-token-456").app.test_client()
        rotated.set_cookie(COOKIE, raw)
        self.assertEqual(rotated.get("/api/data").status_code, 401)
        _load()

    def test_health_stays_open(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
