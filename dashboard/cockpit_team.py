"""Cockpit team overview (data-driven, generic).

Renders the AI-OS agent roster as tiles and reports each gateway's liveness.
Additive by design: registers its own Flask blueprint and reuses the cockpit
token gate. The roster is read from ``team_config.json`` so adding or renaming
an agent needs no code change.

No personal data and no secrets live here. Liveness is a cheap TCP connect to
the gateway port, never an LLM call.
"""

import os
import json
import socket

from flask import Blueprint, jsonify, request, send_file, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTER_PATH = os.path.join(BASE_DIR, "team_config.json")

team_bp = Blueprint("team", __name__)

# Set by init_team(); the blueprint fails closed if never configured.
_AUTH_TOKEN = None


def init_team(app, auth_token):
    """Register the team blueprint on ``app`` and wire the token gate."""
    global _AUTH_TOKEN
    _AUTH_TOKEN = auth_token
    app.register_blueprint(team_bp)
    return team_bp


def _authorized():
    return _AUTH_TOKEN is not None and request.args.get("t") == _AUTH_TOKEN


def load_roster(path=ROSTER_PATH):
    """Return the list of agent dicts from the roster JSON.

    Never raises: a missing or malformed file yields an empty roster so the
    cockpit degrades gracefully instead of 500-ing.
    """
    try:
        with open(path) as fh:
            data = json.load(fh)
        agents = data.get("agents", [])
        return [a for a in agents if isinstance(a, dict) and a.get("key")]
    except Exception:
        return []


def probe_status(port, host="127.0.0.1", timeout=0.4):
    """Cheap liveness probe for an agent gateway.

    Returns 'running' when the TCP port accepts a connection, 'stopped' when it
    refuses, and 'planned' when no port is configured (agent not yet deployed).
    A plain TCP connect avoids spending an LLM API call just to render a dot.
    """
    if not port:
        return "planned"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return "running" if s.connect_ex((host, int(port))) == 0 else "stopped"
    except Exception:
        return "stopped"
    finally:
        try:
            s.close()
        except Exception:
            pass


def _monogram_svg(agent):
    """Deterministic placeholder avatar (no external branding assets)."""
    name = agent.get("name") or agent.get("key") or "?"
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
    gold = "#C6A15B"
    gold_b = "#e7c884"
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' "
        "viewBox='0 0 160 160'>"
        "<defs><radialGradient id='g' cx='50%' cy='38%' r='75%'>"
        "<stop offset='0%' stop-color='#0d1b2f'/>"
        "<stop offset='100%' stop-color='#04101f'/>"
        "</radialGradient></defs>"
        "<rect width='160' height='160' fill='url(#g)'/>"
        f"<circle cx='80' cy='80' r='58' fill='none' stroke='{gold}' "
        "stroke-width='1.5' opacity='0.55'/>"
        f"<circle cx='80' cy='80' r='50' fill='none' stroke='{gold_b}' "
        "stroke-width='0.7' opacity='0.35'/>"
        f"<text x='80' y='80' font-family='sans-serif' font-size='46' "
        f"font-weight='700' fill='{gold_b}' text-anchor='middle' "
        f"dominant-baseline='central'>{initials}</text>"
        "</svg>"
    )
    return svg


@team_bp.route("/api/team")
def api_team():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    roster = load_roster()
    out = []
    for a in roster:
        out.append({
            "key": a.get("key"),
            "name": a.get("name"),
            "role": a.get("role", ""),
            "desc": a.get("desc", ""),
            "accent": a.get("accent", "cyan"),
            "port": a.get("port"),
            "status": probe_status(a.get("port")),
        })
    return jsonify({"agents": out, "count": len(out)})


@team_bp.route("/avatar/<key>")
def avatar(key):
    if not _authorized():
        return "unauthorized", 401
    roster = {a["key"]: a for a in load_roster()}
    agent = roster.get(key)
    if not agent:
        return "not found", 404
    return Response(_monogram_svg(agent), mimetype="image/svg+xml")
