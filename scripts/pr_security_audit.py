#!/usr/bin/env python3
"""PR-Security-Audit: statischer Pre-Merge-Scan eines Unified-Diffs. Meldet
strukturierte JSON-Findings (keine Prosa) zu sicherheitsrelevanten Aenderungen
auf HINZUGEFUEGTEN Zeilen.

Vor dem Merge eines Agenten-PRs will der Security-Agent wissen, ob der Diff
riskante Muster einfuehrt: Secret-shaped Tokens, gefaehrliche Aufrufe
(eval/exec/shell=True/subprocess mit shell), deaktivierte TLS-Verifikation,
weit offene Permissions, neu hinzugefuegte Netz-Endpunkte. Das Tool liest den
Diff (Datei oder stdin), betrachtet NUR '+'-Zeilen (keine Kontext-/Minuszeilen)
und gibt Findings mit Datei, Zeilennummer im neuen File, Schwere und Regel-ID.
Rein lesend, deterministisch, stdlib-only.

Nutzung:
  git diff origin/main...HEAD | python3 scripts/pr_security_audit.py --strict
  python3 scripts/pr_security_audit.py --diff pr.diff

Exit-Codes:
  0  keine HIGH-Findings (oder --strict aus)
  10 mindestens ein HIGH-Finding (nur mit --strict)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# (rule_id, level, regex, message). Secret-Regexe = Quelltext, keine echten Token.
_RULES = [
    ("secret.aws_key", "HIGH", re.compile(r"AKIA[0-9A-Z]{16}"),
     "Moegliches AWS-Access-Key hinzugefuegt"),
    ("secret.github_pat", "HIGH", re.compile(r"ghp_[A-Za-z0-9]{36}"),
     "Moegliches GitHub-PAT hinzugefuegt"),
    ("secret.openai_key", "HIGH", re.compile(r"sk-[A-Za-z0-9]{32,}"),
     "Moegliches API-Key-Token hinzugefuegt"),
    ("secret.private_key", "HIGH", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
     "Private-Key-Block hinzugefuegt"),
    ("exec.eval", "HIGH", re.compile(r"\beval\s*\("),
     "eval() eingefuehrt"),
    ("exec.exec", "HIGH", re.compile(r"\bexec\s*\("),
     "exec() eingefuehrt"),
    ("exec.shell_true", "HIGH", re.compile(r"shell\s*=\s*True"),
     "subprocess mit shell=True eingefuehrt"),
    ("exec.os_system", "HIGH", re.compile(r"\bos\.system\s*\("),
     "os.system() eingefuehrt"),
    ("net.tls_disabled", "HIGH", re.compile(r"verify\s*=\s*False|InsecureRequestWarning|CURLOPT_SSL_VERIFYPEER"),
     "TLS-Verifikation deaktiviert"),
    ("net.pickle", "MEDIUM", re.compile(r"\bpickle\.loads?\s*\("),
     "pickle-Deserialisierung eingefuehrt (RCE-Risiko bei fremden Daten)"),
    ("perm.chmod_777", "MEDIUM", re.compile(r"chmod\s+(?:-R\s+)?0?777|0o777"),
     "Weit offene Dateiberechtigung 777"),
    ("net.new_endpoint", "LOW", re.compile(r"https?://[^\s\"')]+"),
     "Neuer Netz-Endpunkt hinzugefuegt (pruefen)"),
]

_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def audit(diff_text):
    findings = []
    cur_file = None
    new_ln = 0
    for line in (diff_text or "").splitlines():
        mf = _FILE_RE.match(line)
        if mf:
            cur_file = mf.group(1)
            continue
        mh = _HUNK_RE.match(line)
        if mh:
            new_ln = int(mh.group(1))
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            content = line[1:]
            for rule_id, level, rx, msg in _RULES:
                if rx.search(content):
                    findings.append({
                        "rule": rule_id,
                        "level": level,
                        "file": cur_file,
                        "line": new_ln,
                        "message": msg,
                    })
            new_ln += 1
        elif line.startswith("-"):
            # entfernte Zeile: neue Zeilennummer nicht erhoehen
            continue
        else:
            # Kontextzeile
            new_ln += 1

    by_level = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        by_level[f["level"]] = by_level.get(f["level"], 0) + 1
    return {
        "findings": findings,
        "summary": by_level,
        "has_high": by_level["HIGH"] > 0,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Statischer Security-Scan eines Unified-Diffs (JSON-Findings).")
    ap.add_argument("--diff", help="Datei mit dem Unified-Diff (sonst stdin)")
    ap.add_argument("--strict", action="store_true", help="Exit 10 bei HIGH-Findings")
    args = ap.parse_args(argv)

    if args.diff:
        with open(args.diff, "r", encoding="utf-8", errors="ignore") as fh:
            diff_text = fh.read()
    elif not sys.stdin.isatty():
        diff_text = sys.stdin.read()
    else:
        ap.error("kein --diff und kein stdin")
        return 2

    report = audit(diff_text)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and report["has_high"]:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
