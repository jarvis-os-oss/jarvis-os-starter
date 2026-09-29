#!/usr/bin/env python3
"""Blocked-Page-Recovery: klassifiziert eine fehlgeschlagene Web-Antwort und
empfiehlt eine Recovery-Strategie.

Ein Agent, der Webinhalte holt, laeuft regelmaessig in Sperren: 403/429, WAF,
Bot-Wall, Captcha, Paywall. Dieses Tool nimmt Statuscode plus (optional)
Response-Header und Body-Ausschnitt und entscheidet name-agnostisch, WAS die
Sperre ist und WELCHE Gegenmassnahme sinnvoll ist. Es holt selbst nichts aus
dem Netz (rein lesend, deterministisch, stdlib-only) und aendert nichts.

Nutzung:
  python3 scripts/block_detect.py --status 429 --body response.html
  python3 scripts/block_detect.py --status 403 --header-file headers.txt
  echo "<html>...cloudflare...</html>" | python3 scripts/block_detect.py --status 403

Exit-Codes:
  0  Antwort ist NICHT blockiert (oder Klassifikation erfolgreich, --strict aus)
  10 Antwort IST blockiert (nur mit --strict, fuer CI/Automations-Gates)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# (kind, human_reason, [recovery hints]) - reine Heuristik, keine Marken-IDs.
_BODY_SIGNALS = [
    ("captcha", "Captcha-Challenge im Body",
     ["Auf einen echten Browser-Kontext wechseln", "Session/Cookies wiederverwenden"]),
    ("bot_wall", "Bot-/Automations-Erkennung im Body",
     ["Realistischen User-Agent setzen", "Auf headful Browser-Fetch wechseln"]),
    ("waf", "Web-Application-Firewall-Sperre im Body",
     ["Anfragerate senken", "Ueber Browser-Rendering statt Raw-Fetch gehen"]),
    ("paywall", "Paywall-/Login-Wand im Body",
     ["Alternative Quelle suchen", "Nur Metadaten/Snippet verwenden"]),
]

# Body-Substrings (lowercase) -> Signal-Index oben. Generisch gehalten.
_BODY_KEYWORDS = {
    "captcha": 0, "recaptcha": 0, "hcaptcha": 0, "i am not a robot": 0,
    "are you a robot": 1, "unusual traffic": 1, "automated": 1, "bot detected": 1,
    "access denied": 2, "request blocked": 2, "web application firewall": 2,
    "attention required": 2, "ray id": 2, "security check": 2,
    "subscribe to continue": 3, "sign in to read": 3, "premium article": 3,
    "please log in": 3,
}


def classify(status, headers, body):
    """Gibt ein dict mit blocked/kind/reason/recovery zurueck."""
    status = int(status) if status is not None else 0
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    body_l = (body or "").lower()

    reasons = []
    recovery = []
    kind = None
    blocked = False

    if status in (401, 402):
        blocked, kind = True, "auth_or_paywall"
        reasons.append(f"HTTP {status} (Auth/Payment erforderlich)")
        recovery += ["Alternative offene Quelle suchen", "Nur Metadaten verwenden"]
    elif status == 403:
        blocked, kind = True, "forbidden"
        reasons.append("HTTP 403 (Zugriff verweigert, oft WAF/Bot-Wall)")
        recovery += ["Realistischen User-Agent setzen", "Auf Browser-Fetch wechseln"]
    elif status == 429:
        blocked, kind = True, "rate_limited"
        reasons.append("HTTP 429 (Rate-Limit)")
        ra = headers.get("retry-after")
        if ra:
            reasons.append(f"Retry-After: {ra}")
        recovery += ["Backoff und spaeter erneut versuchen", "Anfragerate senken"]
    elif status in (503, 520, 521, 522, 523, 526):
        blocked, kind = True, "edge_challenge"
        reasons.append(f"HTTP {status} (Edge/Challenge-Antwort)")
        recovery += ["Ueber Browser-Rendering gehen", "Backoff und erneut versuchen"]

    # Body-Signale ergaenzen die Klassifikation auch bei 200 (soft-block).
    hit = set()
    for kw, idx in _BODY_KEYWORDS.items():
        if kw in body_l and idx not in hit:
            hit.add(idx)
            sig = _BODY_SIGNALS[idx]
            blocked = True
            if kind is None:
                kind = sig[0]
            reasons.append(sig[1])
            recovery += sig[2]

    # dedupe recovery, Reihenfolge erhalten
    seen = set()
    recovery = [r for r in recovery if not (r in seen or seen.add(r))]

    if not blocked:
        kind = "ok"
        reasons.append("Keine Sperr-Signale erkannt")

    return {
        "blocked": blocked,
        "kind": kind,
        "status": status,
        "reasons": reasons,
        "recovery": recovery,
    }


def _parse_headers(text):
    out = {}
    for line in (text or "").splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Klassifiziert eine blockierte Web-Antwort.")
    ap.add_argument("--status", type=int, required=True, help="HTTP-Statuscode")
    ap.add_argument("--body", help="Datei mit Response-Body (sonst stdin, sonst leer)")
    ap.add_argument("--header-file", help="Datei mit Response-Headern (eine pro Zeile: Name: Wert)")
    ap.add_argument("--strict", action="store_true", help="Exit 10 wenn blockiert (fuer Gates)")
    args = ap.parse_args(argv)

    body = ""
    if args.body:
        with open(args.body, "r", encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
    elif not sys.stdin.isatty():
        body = sys.stdin.read()

    headers = {}
    if args.header_file:
        with open(args.header_file, "r", encoding="utf-8", errors="ignore") as fh:
            headers = _parse_headers(fh.read())

    result = classify(args.status, headers, body)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and result["blocked"]:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
