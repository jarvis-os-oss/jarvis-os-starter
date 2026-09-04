#!/usr/bin/env python3
"""Scan the repository for secrets and personal-data leakage.

Fails (exit 1) if any tracked file matches a known secret pattern, a routable
public IP, or a denylisted personal / company token. Intended for local runs
and CI. Pure standard library, no dependencies.

Two independent layers guard the tree:

  1. PATTERN + DENYLIST pass (per-file). Secret-shaped regexes plus a denylist
     of literal owner names / companies / domains. The denylist ships with
     GENERIC placeholders only; real owner-specific terms are loaded at runtime
     from an untracked, git-ignored file (``.scan_denylist.local``) so no real
     personal data ever lives in committed code. This pass exempts the scanner
     itself and ``.env.example`` (both legitimately hold example tokens).

  2. STRUCTURAL pass (every file, NO exemptions -- not even this scanner). It
     flags routable public IPv4 addresses and secret-shaped tokens regardless
     of any denylist. This is the safety net for the self-exclude blind spot:
     even if someone hardcodes a real production IP into this very file, layer 2
     still catches it because it never exempts anything.

Usage:
  python3 scripts/scan_secrets.py            # scan git-tracked files
  python3 scripts/scan_secrets.py --all      # scan the whole working tree
"""

import argparse
import ipaddress
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Layer 1 exempts this scanner (it legitimately lists example patterns/terms).
# Layer 2 (structural) never exempts anything, including this file.
SELF = os.path.abspath(__file__)

# Files/dirs never scanned (binary, vcs, this scanner, the example env).
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
# .env.example is allowed to hold placeholder-looking values by design.
SKIP_FILES = {os.path.join(ROOT, ".env.example")}

# Untracked, git-ignored file holding the OWNER's real denylist terms. It never
# enters version control; a committed .example shows the format.
LOCAL_DENYLIST_FILE = os.path.join(ROOT, ".scan_denylist.local")

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

# GENERIC placeholder denylist shipped in the repo. These are NOT real. Each
# instance replaces / extends them via the git-ignored .scan_denylist.local.
# Kept deliberately generic so the committed codebase carries no real names.
DENYLIST_DEFAULT = [
    "example-corp",
    "acme-inc",
    "your-company-name",
    "your-name-here",
]
# Note: "example.com" is intentionally NOT denylisted. It is the RFC2606
# reserved documentation domain, a legitimate placeholder (the shipped
# .env.example uses cockpit.example.com by design, and setup.py copies that
# value into the generated runtime .env). Flagging it produced false positives
# and is inconsistent with is_public_ip(), which already treats the RFC5737
# documentation IP ranges as safe placeholders. Real owner domains are caught
# via the git-ignored .scan_denylist.local, and layer 2 still catches any
# real secret regardless of denylist.

# Any IPv4 literal, checked structurally against reserved ranges below.
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def load_denylist():
    """Generic defaults plus any owner terms from the git-ignored local file."""
    terms = list(DENYLIST_DEFAULT)
    try:
        with open(LOCAL_DENYLIST_FILE, "r", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    terms.append(line)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return terms


def is_public_ip(text):
    """True if the IPv4 string is a routable public address.

    Private, loopback, link-local, multicast, reserved and the RFC5737
    documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) are
    all treated as safe placeholders and NOT flagged.
    """
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return False
    if not isinstance(ip, ipaddress.IPv4Address):
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
        return False
    if ip.is_reserved or ip.is_unspecified:
        return False
    # RFC5737 documentation ranges are explicit placeholders.
    for net in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"):
        if ip in ipaddress.ip_network(net):
            return False
    return True


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
    denylist = load_denylist()
    deny_re = re.compile("|".join(re.escape(w) for w in denylist), re.IGNORECASE) if denylist else None

    for path in paths:
        try:
            with open(path, "r", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            continue

        abspath = os.path.abspath(path)
        layer1_exempt = abspath == SELF or path in SKIP_FILES

        # --- Layer 2: structural pass. Runs on EVERY file, no exemptions. ---
        for label, rx in SECRET_PATTERNS:
            for m in rx.finditer(text):
                findings.append((path, label, m.group(0)[:12] + "..."))
        for m in IPV4_RE.finditer(text):
            if is_public_ip(m.group(0)):
                findings.append((path, "Routable public IP", m.group(0)))

        # --- Layer 1: denylist literals. Skips scanner + .env.example. ---
        if layer1_exempt or deny_re is None:
            continue
        for m in deny_re.finditer(text):
            findings.append((path, "DENYLISTED personal/company token", m.group(0)))
    return findings


def dedupe(findings):
    seen = set()
    out = []
    for f in findings:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="scan the whole tree, not just tracked files")
    args = ap.parse_args(argv)

    paths = walk_files() if args.all else (tracked_files() or walk_files())
    findings = dedupe(scan(paths))
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
