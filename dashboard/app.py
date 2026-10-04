"""AI-OS cockpit dashboard (generic starter skeleton).

A minimal token-gated Flask app that renders the agent team and a system
overview. It carries NO personal data, NO branding assets, and NO secrets. All
configuration comes from environment variables (see .env.example).

Endpoints:
  GET /                -> the cockpit UI (token-gated)
  GET /api/health      -> unauthenticated liveness probe (for the watchdog)
  GET /api/data?t=...  -> cockpit payload (time, agent count, config)
  GET /api/team?t=...  -> agent roster with live status (cockpit_team blueprint)
  GET /avatar/<key>?t= -> generated monogram avatar (cockpit_team blueprint)
  POST /api/chat?t=... -> route a message to an agent gateway (optional)

Token gate: every route except /api/health checks ?t=<COCKPIT_TOKEN> and fails
closed. The token is read from the environment, never from a committed file.
After a first login (?t= or POST /login) a signed HttpOnly cookie keeps the
session, so the bare URL works afterwards and survives restarts.
"""

import os
import sys
import json
import hashlib
import hmac
import urllib.request
from datetime import datetime

from flask import Flask, jsonify, send_file, request, redirect
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_auth_token():
    """Cockpit access token from the environment. Fail closed.

    Never falls back to an open or default value: if COCKPIT_TOKEN is unset the
    cockpit refuses to serve anything but /api/health.
    """
    return os.environ.get("COCKPIT_TOKEN", "").strip()


AUTH_TOKEN = _load_auth_token()

# --- cookie login (signed HttpOnly cookie, additive to the ?t= gate) --------
# The raw token is never stored in the cookie: a token-bound hash is signed, so
# rotating COCKPIT_TOKEN invalidates every old cookie. The signing key comes from
# COCKPIT_SECRET_KEY, else it is derived from the token, so it is stable across
# restarts without writing any file. No token configured: no cookie is ever valid.
COOKIE_NAME = "cockpit_auth"
COOKIE_MAX_AGE = 30 * 24 * 3600


def _signing_key():
    key = os.environ.get("COCKPIT_SECRET_KEY", "").strip()
    if key:
        return key
    return hashlib.sha256(("cockpit-cookie-key-v1:" + AUTH_TOKEN).encode()).hexdigest()


_signer = TimestampSigner(_signing_key(), salt="cockpit-auth-v1")


def _cookie_payload():
    return hashlib.sha256(("cockpit-auth-v1:" + AUTH_TOKEN).encode()).hexdigest()


def _cookie_valid(raw):
    if not AUTH_TOKEN or not raw:
        return False
    try:
        data = _signer.unsign(raw, max_age=COOKIE_MAX_AGE)
        return hmac.compare_digest(data.decode("utf-8"), _cookie_payload())
    except (BadSignature, SignatureExpired, Exception):
        return False


@app.before_request
def _cookie_auth_gate():
    """If no valid ?t= is present but a valid cookie is, inject the token so all
    existing gates (here and in blueprints) pass unchanged. Fail closed."""
    try:
        if not AUTH_TOKEN or request.args.get("t") == AUTH_TOKEN:
            return None
        if _cookie_valid(request.cookies.get(COOKIE_NAME)):
            args = request.args.copy()
            args["t"] = AUTH_TOKEN
            request.args = args
    except Exception:
        pass
    return None


@app.after_request
def _cookie_auth_set(resp):
    """Set the cookie after a real login (token in the query string or /login POST)."""
    try:
        real = getattr(request, "_cockpit_login_ok", False) or (
            bool(AUTH_TOKEN)
            and request.args.get("t") == AUTH_TOKEN
            and ("t=" + AUTH_TOKEN) in request.query_string.decode("latin-1", "ignore")
        )
        if real and not _cookie_valid(request.cookies.get(COOKIE_NAME)):
            secure = request.is_secure or request.headers.get("X-Forwarded-Proto", "") == "https"
            resp.set_cookie(COOKIE_NAME, _signer.sign(_cookie_payload().encode()).decode(),
                            max_age=COOKIE_MAX_AGE, httponly=True, secure=secure,
                            samesite="Lax", path="/")
    except Exception:
        pass
    return resp


_LOGIN_FORM = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Cockpit Login</title></head>"
    "<body style='font-family:monospace;background:#0a0e17;color:#ccc;"
    "text-align:center;padding-top:18vh;height:100vh;margin:0'>"
    "<h1 style='font-size:1.3rem'>Cockpit</h1>{msg}"
    "<form method='post' action='/login' style='margin-top:1.5rem'>"
    "<input type='password' name='t' placeholder='Access token' autofocus "
    "style='padding:.6rem;width:16rem;max-width:80vw'><br>"
    "<button type='submit' style='margin-top:1rem;padding:.6rem 1.4rem'>Sign in</button>"
    "</form></body></html>"
)


@app.route("/login", methods=["GET", "POST"])
def login():
    if AUTH_TOKEN and request.args.get("t") == AUTH_TOKEN:
        return redirect("/")
    if request.method == "POST":
        supplied = (request.form.get("t") or "").strip()
        if AUTH_TOKEN and supplied and hmac.compare_digest(supplied, AUTH_TOKEN):
            request._cockpit_login_ok = True
            return redirect("/")
        return _LOGIN_FORM.format(msg="<p style='color:#e23636'>Wrong token.</p>"), 401
    return _LOGIN_FORM.format(msg=""), 200


# Agent gateway base: the orchestrator (default profile). Used only if /api/chat is wired.
AGENT_API = os.environ.get("ORCHESTRATOR_API_URL", "http://127.0.0.1:8642/v1/chat/completions")


def _agent_key():
    return os.environ.get("API_SERVER_KEY", "").strip()


def _authorized():
    return bool(AUTH_TOKEN) and request.args.get("t") == AUTH_TOKEN


# --- team blueprint (data-driven roster + status) ---------------------------
try:
    from cockpit_team import init_team, load_roster
    init_team(app, AUTH_TOKEN)
except Exception as _e:  # pragma: no cover - defensive
    print(f"[cockpit] team module not loaded: {_e}", file=sys.stderr)

    def load_roster():
        return []


@app.route("/api/health")
def health():
    """Unauthenticated liveness probe for the watchdog and container HEALTHCHECK."""
    return jsonify({"status": "ok", "service": "aios-cockpit"})


@app.route("/api/data")
def data():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    roster = load_roster()
    return jsonify({
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%A, %d. %B %Y"),
        "agent_count": len(roster),
        "instance": os.environ.get("AIOS_INSTANCE_NAME", "AI-OS"),
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Optional: route a message to an agent gateway.

    Off by default in the starter kit: without a running Hermes gateway and an
    API_SERVER_KEY this returns 502. Wire it up per your deployment.
    """
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(force=True, silent=True) or {}
    msg = (body.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "empty"}), 400
    bearer = _agent_key()
    if not bearer:
        return jsonify({"error": "agent gateway not configured"}), 502
    payload = json.dumps({
        "model": "hermes-agent",
        "messages": [{"role": "user", "content": msg}],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        AGENT_API, data=payload,
        headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=280)
        d = json.loads(r.read())
        return jsonify({"reply": d["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 502


@app.route("/")
def index():
    if not _authorized():
        return ("<h1 style='font-family:monospace;color:#e23636;background:#0a0e17;"
                "text-align:center;padding-top:20vh;height:100vh'>ACCESS DENIED</h1>"), 401
    return send_file(os.path.join(BASE_DIR, "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("COCKPIT_PORT", "8517"))
    app.run(host="0.0.0.0", port=port)
