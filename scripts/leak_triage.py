#!/usr/bin/env python3
"""Credential-Leak-Response: erkennt in einem Text/Log/Notiz-Blob geleakte
Secrets, klassifiziert sie und gibt einen Sofortmassnahmen-Plan aus.

Wenn ein Klartext-Secret in Daten, Notizen oder Logs auftaucht, muss der
Betreiber (oder sein Security-Agent) schnell wissen: WAS ist geleakt und WAS
ist jetzt zu tun (rotieren, widerrufen, Historie pruefen). Dieses Tool nimmt
einen Blob (Datei oder stdin), matcht ihn gegen Secret-Muster und liefert je
Fund einen redigierten Nachweis plus generische Response-Schritte.

WICHTIG: Das Tool gibt Secrets NIE im Klartext aus. Treffer werden redigiert
(nur erste/letzte Zeichen). Rein lesend, stdlib-only, kein Netzzugriff.

Nutzung:
  python3 scripts/leak_triage.py --input notes.txt
  cat some.log | python3 scripts/leak_triage.py --strict

Exit-Codes:
  0  kein Secret erkannt (oder --strict aus)
  10 mindestens ein Secret erkannt (nur mit --strict)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# (label, regex, response-hint). Muster als Regex-Quelltext, keine echten Token.
_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"),
     "AWS-Key in IAM sofort deaktivieren und rotieren, CloudTrail pruefen"),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
     "Schluesselpaar neu erzeugen, alten Public-Key ueberall entfernen"),
    ("github_pat_classic", re.compile(r"ghp_[A-Za-z0-9]{36}"),
     "GitHub-Token widerrufen (Settings/Developer), neues Token mit engem Scope"),
    ("github_pat_fine", re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),
     "Fine-grained-Token widerrufen und neu ausstellen"),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
     "Slack-Token in der App-Config rotieren"),
    ("openai_style_key", re.compile(r"sk-[A-Za-z0-9]{32,}"),
     "API-Key beim Provider widerrufen und neu erzeugen"),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
     "Google-API-Key in der Cloud-Console rotieren und Restriktionen setzen"),
    ("bearer_jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
     "Signing-Secret rotieren, ausgestellte Tokens invalidieren"),
]


def _redact(token):
    if len(token) <= 8:
        return token[0] + "***"
    return token[:4] + "***" + token[-2:]


def scan(text):
    findings = []
    for label, rx, hint in _PATTERNS:
        for m in rx.finditer(text or ""):
            tok = m.group(0)
            line_no = text.count("\n", 0, m.start()) + 1
            findings.append({
                "type": label,
                "line": line_no,
                "redacted": _redact(tok),
                "response": hint,
            })
    return {
        "leaked": bool(findings),
        "count": len(findings),
        "findings": findings,
        "general_steps": [
            "1. Betroffenes Secret sofort rotieren/widerrufen (siehe response je Fund)",
            "2. Quelle des Leaks bereinigen (Datei/Log/Notiz), auch aus Backups/Caches",
            "3. Wenn in Git: Historie pruefen und ggf. purgen, force-push nach Freigabe",
            "4. Zugriffs-/Audit-Logs auf Missbrauch im Leak-Zeitfenster pruefen",
            "5. Vorfall an den Betreiber eskalieren",
        ] if findings else [],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Erkennt und triagiert geleakte Secrets in einem Blob.")
    ap.add_argument("--input", help="Datei mit dem zu pruefenden Text (sonst stdin)")
    ap.add_argument("--strict", action="store_true", help="Exit 10 wenn ein Secret gefunden wird")
    args = ap.parse_args(argv)

    if args.input:
        with open(args.input, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        ap.error("kein --input und kein stdin")
        return 2

    report = scan(text)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and report["leaked"]:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
