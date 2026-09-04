#!/usr/bin/env python3
"""Scan the repository for secrets and personal-data leakage.

Fails (exit 1) if any tracked file matches a known secret pattern or a
denylisted personal / company token. Intended for local runs and CI. Pure
standard library, no dependencies.

Usage:
  python3 scripts/scan_secrets.py            # scan git-tracked files
  python3 scripts/scan_secrets.py --all      # scan the whole working tree
"""

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# This scanner is allowed to contain the patterns it searches for.
SELF = os.path.abspath(__file__)

# Files/dirs never scanned (binary, vcs, this scanner, the example env).
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
# .env.example is allowed to hold placeholder-looking values by design.
SKIP_FILES = {os.path.join(ROOT, ".env.example")}

# Secret-shaped patterns. Each is (label, compiled regex).
SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub PAT (classic)", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub fine-grained PAT", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("OpenAI-style key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Bearer JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

# Personal / company denylist. These MUST NEVER appear in this generic repo.
# Kept generic-neutral in the codebase; this list is the guard rail.
DENYLIST = [
    "REDACTED", "REDACTED", "REDACTED", "REDACTED",
    "REDACTED", "REDACTED", "REDACTED", "REDACTED", "REDACTED",
]
DENY_RE = re.compile("|".join(re.escape(w) for w in DENYLIST), re.IGNORECASE)


def tracked_files():
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, check=True
        ).stdout
        return [os.path.join(ROOT, p) for p in out.splitlines() if p.strip()]
    except Exception:
        return None


def walk_files():
    files = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            files.append(os.path.join(base, n))
    return files


def scan(paths):
    findings = []
    for path in paths:
        if os.path.abspath(path) == SELF or path in SKIP_FILES:
            continue
        try:
            with open(path, "r", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            continue
        for label, rx in SECRET_PATTERNS:
            for m in rx.finditer(text):
                findings.append((path, label, m.group(0)[:12] + "..."))
        for m in DENY_RE.finditer(text):
            findings.append((path, "DENYLISTED personal/company token", m.group(0)))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="scan the whole tree, not just tracked files")
    args = ap.parse_args(argv)

    paths = walk_files() if args.all else (tracked_files() or walk_files())
    findings = scan(paths)
    if findings:
        print("SECRET/PII SCAN FAILED:")
        for path, label, snippet in findings:
            rel = os.path.relpath(path, ROOT)
            print(f"  {rel}: {label}: {snippet}")
        return 1
    print(f"SECRET/PII SCAN OK: {len(paths)} files clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
