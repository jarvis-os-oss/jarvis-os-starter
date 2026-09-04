"""JARVIS-OS cockpit dashboard (generic starter skeleton).

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
"""

import os
import sys
import json
import urllib.request
from datetime import datetime

from flask import Flask, jsonify, send_file, request

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

# Agent gateway base: JARVIS (default profile). Used only if /api/chat is wired.
AGENT_API = os.environ.get("JARVIS_API_URL", "http://127.0.0.1:8642/v1/chat/completions")


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
    return jsonify({"status": "ok", "service": "jarvis-os-cockpit"})


@app.route("/api/data")
def data():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    roster = load_roster()
    return jsonify({
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%A, %d. %B %Y"),
        "agent_count": len(roster),
        "instance": os.environ.get("AIOS_INSTANCE_NAME", "JARVIS-OS"),
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
