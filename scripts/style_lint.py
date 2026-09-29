#!/usr/bin/env python3
"""Konfigurierbares Style-/Policy-Lint-Gate.

Ein generisches, KONFIGURIERBARES Gate, das verbotene Zeichen oder Muster in
Textdateien blockiert (pre-commit oder CI). Die Regeln stehen komplett in einer
Config-Datei, damit jede Instanz ihre eigene Policy definiert. Als Beispiel-
Regel ist ein Em-Dash/En-Dash-Verbot vordefiniert (eine verbreitete
Stil-Praeferenz), das kann aber frei geaendert oder ersetzt werden.

Regeltypen:
  substring  literales Vorkommen (case-sensitiv, sofern nicht ignore_case)
  regex      Python-Regex

Config (siehe scripts/style_lint.json), ships DISABLED:
  {
    "enabled": false,
    "include_globs": ["**/*.md", "**/*.txt"],
    "exclude_globs": ["**/vendor/**"],
    "rules": [
      {"id": "no-emdash", "type": "substring", "pattern": "\u2014",
       "message": "Em-Dash nicht erlaubt (Beispiel-Regel)"}
    ]
  }

DISABLED-Default: ohne "enabled": true meldet das Gate nur, dass es aus ist, und
gibt Exit 0. Nichts blockiert eine frische Installation ungefragt.

Exit-Codes:
  0  sauber (oder deaktiviert)
  1  mindestens eine Regelverletzung
  2  Nutzungs-/Konfigurationsfehler
"""
from __future__ import annotations

import argparse
import fnmatch
import glob as globmod
import json
import os
import re
import sys


def _log(msg: str) -> None:
    print(msg, flush=True)


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _match_any(rel: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(os.path.basename(rel), pat):
            return True
    return False


def _collect_files(root: str, include: list[str], exclude: list[str]) -> list[str]:
    files = []
    for pat in include:
        for p in globmod.glob(os.path.join(root, pat), recursive=True):
            if os.path.isfile(p):
                files.append(p)
    seen = set()
    out = []
    for p in files:
        rel = os.path.relpath(p, root)
        if rel in seen:
            continue
        seen.add(rel)
        if exclude and _match_any(rel, exclude):
            continue
        out.append(p)
    return sorted(out)


def _compile_rules(rules: list[dict]):
    compiled = []
    for r in rules:
        rid = r.get("id", "?")
        rtype = r.get("type", "substring")
        pattern = r.get("pattern", "")
        message = r.get("message", f"Regel {rid} verletzt")
        ignore_case = bool(r.get("ignore_case", False))
        if rtype == "regex":
            flags = re.IGNORECASE if ignore_case else 0
            compiled.append((rid, "regex", re.compile(pattern, flags), message,
                             ignore_case))
        else:
            compiled.append((rid, "substring", pattern, message, ignore_case))
    return compiled


def _check_text(text: str, compiled) -> list[tuple[int, str, str]]:
    """Gibt (Zeilennummer, rule_id, message) je Verletzung zurueck."""
    hits = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        for rid, rtype, pat, message, ignore_case in compiled:
            if rtype == "regex":
                if pat.search(line):
                    hits.append((lineno, rid, message))
            else:
                hay = line.lower() if ignore_case else line
                needle = pat.lower() if ignore_case else pat
                if needle and needle in hay:
                    hits.append((lineno, rid, message))
    return hits


def run(config: dict, root: str, files: list[str] | None) -> int:
    if not config.get("enabled", False):
        _log("Style-Lint-Gate deaktiviert (enabled=false), keine Pruefung")
        return 0
    rules = config.get("rules", [])
    if not rules:
        _log("keine Regeln konfiguriert")
        return 0
    compiled = _compile_rules(rules)

    if files:
        targets = [f for f in files if os.path.isfile(f)]
    else:
        include = config.get("include_globs", ["**/*.md", "**/*.txt"])
        exclude = config.get("exclude_globs", [])
        targets = _collect_files(root, include, exclude)

    total_hits = 0
    for path in targets:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        for lineno, rid, message in _check_text(text, compiled):
            rel = os.path.relpath(path, root)
            _log(f"  {rel}:{lineno}: [{rid}] {message}")
            total_hits += 1

    if total_hits:
        _log(f"\nSTYLE-LINT FEHLGESCHLAGEN: {total_hits} Verletzung(en) in "
             f"{len(targets)} geprueften Dateien.")
        return 1
    _log(f"STYLE-LINT OK: {len(targets)} Dateien sauber.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Konfigurierbares Style-/Policy-Lint-Gate")
    ap.add_argument("--config", required=True, help="Pfad zur style_lint.json")
    ap.add_argument("--root", default=".", help="Basisverzeichnis fuer die Globs")
    ap.add_argument("files", nargs="*",
                    help="optional: konkrete Dateien pruefen (statt der Globs), "
                         "z.B. die im Commit geaenderten")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.config):
        _log(f"Config nicht gefunden: {args.config}")
        return 2
    try:
        config = _load(args.config)
    except (json.JSONDecodeError, OSError) as e:
        _log(f"Config ungueltig: {e}")
        return 2
    return run(config, args.root, args.files or None)


if __name__ == "__main__":
    sys.exit(main())
