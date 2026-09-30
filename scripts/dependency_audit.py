#!/usr/bin/env python3
"""Dependency-Security-Audit: statische, offline Risiko-Pruefung einer
Dependency-Manifest-Datei, BEVOR eine fremde Abhaengigkeit adoptiert wird.

Adoptiert ein Agent (oder sein Betreiber) ein Drittanbieter-Paket, will man
vor der Installation wissen: ist die Version gepinnt, kommt sie aus einer
vertrauenswuerdigen Quelle, gibt es verdaechtige Install-Hooks. Dieses Tool
liest das Manifest (requirements.txt / package.json / pyproject-Ausschnitt)
und meldet Risikosignale. Es installiert NICHTS und ruft kein Netz auf
(rein lesend, deterministisch, stdlib-only).

Erkannte Signale (name-agnostisch, heuristisch):
  * ungepinnte Version (kein ==, offene Range, "*", "latest")
  * direkte VCS-/URL-Quelle (git+, http(s) tarball) statt Registry
  * lokale/relative Pfadquelle
  * (package.json) lifecycle-Hooks preinstall/postinstall/install

Nutzung:
  python3 scripts/dependency_audit.py --manifest requirements.txt
  python3 scripts/dependency_audit.py --manifest package.json --strict

Exit-Codes:
  0  keine hoch bewerteten Risiken (oder --strict aus)
  10 mindestens ein HIGH-Risiko (nur mit --strict)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

_VCS_RE = re.compile(r"^(git\+|hg\+|svn\+|bzr\+)|\.git(@|#|$)", re.IGNORECASE)
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_PINNED_RE = re.compile(r"==\s*\d")
_OPEN_RANGE = re.compile(r"(>=|>|\^|~|\*|latest)", re.IGNORECASE)
_HOOKS = ("preinstall", "install", "postinstall")


def _finding(dep, level, reason):
    return {"dependency": dep, "level": level, "reason": reason}


def audit_requirements(text):
    findings = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            # -r/-e/-c Direktiven separat behandeln
            if line.lower().startswith("-e") or "file://" in line.lower():
                findings.append(_finding(line, "HIGH", "Editable/lokale Pfadquelle"))
            continue
        low = line.lower()
        if _VCS_RE.search(low) or _URL_RE.search(low):
            findings.append(_finding(line, "HIGH", "Direkte VCS-/URL-Quelle statt Registry"))
            continue
        if not _PINNED_RE.search(line):
            if _OPEN_RANGE.search(line) or re.match(r"^[A-Za-z0-9._-]+$", line):
                findings.append(_finding(line, "MEDIUM", "Version nicht exakt gepinnt (kein ==)"))
    return findings


def audit_package_json(text):
    findings = []
    data = json.loads(text)
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        for name, spec in (data.get(section) or {}).items():
            spec_s = str(spec)
            low = spec_s.lower()
            if _VCS_RE.search(low) or _URL_RE.search(low):
                findings.append(_finding(f"{name}:{spec_s}", "HIGH", "VCS-/URL-Quelle statt Registry"))
            elif low.startswith("file:") or low.startswith("link:"):
                findings.append(_finding(f"{name}:{spec_s}", "HIGH", "Lokale Pfadquelle"))
            elif spec_s in ("*", "latest") or _OPEN_RANGE.search(spec_s) or not re.match(r"^\d", spec_s):
                findings.append(_finding(f"{name}:{spec_s}", "MEDIUM", "Version nicht exakt gepinnt"))
    scripts = data.get("scripts") or {}
    for hook in _HOOKS:
        if hook in scripts:
            findings.append(_finding(f"scripts.{hook}", "HIGH",
                                     "Lifecycle-Install-Hook fuehrt beim Installieren Code aus"))
    return findings


def audit(path, text):
    name = os.path.basename(path).lower()
    if name == "package.json":
        findings = audit_package_json(text)
    else:
        findings = audit_requirements(text)
    levels = {f["level"] for f in findings}
    return {
        "manifest": os.path.basename(path),
        "high": sum(1 for f in findings if f["level"] == "HIGH"),
        "medium": sum(1 for f in findings if f["level"] == "MEDIUM"),
        "findings": findings,
        "has_high": "HIGH" in levels,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline-Risikoscan eines Dependency-Manifests.")
    ap.add_argument("--manifest", required=True, help="Pfad zu requirements.txt oder package.json")
    ap.add_argument("--strict", action="store_true", help="Exit 10 bei HIGH-Risiko")
    args = ap.parse_args(argv)

    with open(args.manifest, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    report = audit(args.manifest, text)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and report["has_high"]:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
