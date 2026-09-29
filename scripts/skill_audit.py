#!/usr/bin/env python3
"""Skill-Library-Kuration: findet Wildwuchs, schlaegt vor, loescht NIE.

Jede skill-nutzende Instanz sammelt mit der Zeit doppelte, veraltete oder
uebergrosse Skills an. Dieses Tool inspiziert ein Skill-Verzeichnis (SKILL.md
je Skill, optional in Kategorie-Unterordnern) und meldet:

  * OVERSIZE   SKILL.md groesser als --max-lines Zeilen (Kandidat fuer Split).
  * DUP_NAME   mehrere Skills mit demselben Namen (Frontmatter oder Verzeichnis).
  * DUP_DESC   sehr aehnliche Beschreibungen (moegliche Redundanz).
  * STALE      seit mehr als --stale-days nicht geaendert (nur Hinweis).
  * NO_DESC    fehlende/leere description im Frontmatter.

Es gibt NUR Empfehlungen aus (kein Auto-Delete, kein Auto-Split). Rein lesend.
stdlib-only.

Ausgabe: Text (Default) oder --format json.

Exit-Codes:
  0  keine Befunde
  1  mindestens ein Befund (nur informativ; Auswertung beim Betreiber)
  2  Nutzungs-/Eingabefehler
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from difflib import SequenceMatcher


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def _parse_frontmatter(text: str) -> dict:
    """Minimaler YAML-Frontmatter-Parser (name/description), stdlib-only."""
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    if end == -1:
        return meta
    block = text[3:end]
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            key = k.strip().lower()
            if key in ("name", "description"):
                meta[key] = v.strip().strip('"').strip("'")
    return meta


def _find_skills(root: str) -> list[dict]:
    skills = []
    for base, _dirs, names in os.walk(root):
        for n in names:
            if n != "SKILL.md":
                continue
            path = os.path.join(base, n)
            text = _read(path)
            meta = _parse_frontmatter(text)
            dir_name = os.path.basename(os.path.dirname(path))
            skills.append({
                "path": path,
                "dir": dir_name,
                "name": meta.get("name", dir_name),
                "description": meta.get("description", ""),
                "lines": text.count("\n") + 1 if text else 0,
                "mtime": os.path.getmtime(path) if os.path.isfile(path) else 0,
            })
    return skills


def audit(skills: list[dict], max_lines: int, stale_days: int,
          desc_threshold: float) -> list[dict]:
    findings = []
    now = time.time()

    by_name = defaultdict(list)
    for s in skills:
        by_name[s["name"].lower()].append(s)
        if s["lines"] > max_lines:
            findings.append({"type": "OVERSIZE", "skill": s["name"],
                             "detail": f"{s['lines']} Zeilen (> {max_lines})"})
        if not s["description"]:
            findings.append({"type": "NO_DESC", "skill": s["name"],
                             "detail": "leere/fehlende description"})
        if stale_days > 0 and s["mtime"] and (now - s["mtime"]) > stale_days * 86400:
            days = int((now - s["mtime"]) / 86400)
            findings.append({"type": "STALE", "skill": s["name"],
                             "detail": f"seit {days} Tagen unveraendert"})

    for name, group in by_name.items():
        if len(group) > 1:
            findings.append({"type": "DUP_NAME", "skill": name,
                             "detail": f"{len(group)} Skills mit gleichem Namen"})

    # Aehnliche Beschreibungen (paarweise, nur nicht-leere).
    described = [s for s in skills if s["description"]]
    for i in range(len(described)):
        for j in range(i + 1, len(described)):
            a, b = described[i], described[j]
            if a["name"].lower() == b["name"].lower():
                continue
            ratio = SequenceMatcher(None, a["description"].lower(),
                                    b["description"].lower()).ratio()
            if ratio >= desc_threshold:
                findings.append({
                    "type": "DUP_DESC",
                    "skill": f"{a['name']} ~ {b['name']}",
                    "detail": f"Beschreibungen {int(ratio * 100)}% aehnlich",
                })
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Skill-Library-Kuration (nur Vorschlaege)")
    ap.add_argument("root", help="Wurzelverzeichnis der Skills (enthaelt SKILL.md je Skill)")
    ap.add_argument("--max-lines", type=int, default=500,
                    help="OVERSIZE-Schwelle in Zeilen (Default 500)")
    ap.add_argument("--stale-days", type=int, default=0,
                    help="STALE-Schwelle in Tagen (0 = aus)")
    ap.add_argument("--desc-threshold", type=float, default=0.85,
                    help="Aehnlichkeitsschwelle fuer DUP_DESC (0..1, Default 0.85)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"Verzeichnis nicht gefunden: {args.root}", flush=True)
        return 2

    skills = _find_skills(args.root)
    findings = audit(skills, args.max_lines, args.stale_days, args.desc_threshold)

    if args.format == "json":
        print(json.dumps({"scanned": len(skills), "findings": findings}, indent=2))
        return 1 if findings else 0

    print(f"Skill-Kuration: {len(skills)} Skills gescannt.")
    if not findings:
        print("OK: keine Befunde.")
        return 0
    for f in findings:
        print(f"  [{f['type']}] {f['skill']}: {f['detail']}")
    print(f"\n{len(findings)} Vorschlaege. Kein Auto-Delete/Split, Auswertung "
          f"liegt beim Betreiber.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
