#!/usr/bin/env python3
"""Grounded-Citations: prueft, ob die Aussagen einer Antwort durch zitierte
Quellen gedeckt sind.

Ein Agent, der recherchiert und dann zusammenfasst, soll jede Sachaussage mit
einer Quelle belegen. Dieses Tool nimmt einen Antworttext mit Inline-Markern
(Default `[n]`) und eine Quellenliste (id -> snippet) und meldet:
  * Saetze ohne jeden Zitat-Marker (ungegrounded),
  * Marker, die auf eine nicht existierende Quelle zeigen (dangling),
  * optional: Marker, deren Aussage-Tokens NICHT im Quellen-Snippet vorkommen
    (schwacher Overlap-Check, --min-overlap).

Rein lesend, deterministisch, stdlib-only. Aendert nichts.

Nutzung:
  python3 scripts/citation_check.py --answer answer.txt --sources sources.json
  python3 scripts/citation_check.py --answer answer.txt --sources sources.json --min-overlap 0.15 --strict

sources.json: {"1": "quelltext ...", "2": "..."}

Exit-Codes:
  0  alles gegrounded (oder --strict aus)
  10 Grounding-Maengel gefunden (nur mit --strict)
  2  Nutzungsfehler
"""
from __future__ import annotations

import argparse
import json
import re
import sys

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)


def _tokens(text):
    return set(w.lower() for w in _WORD.findall(text or ""))


def check(answer, sources, marker=r"\[(\w+)\]", min_overlap=0.0):
    """Gibt einen Report als dict zurueck."""
    marker_re = re.compile(marker)
    sources = {str(k): v for k, v in (sources or {}).items()}

    ungrounded = []   # Saetze ganz ohne Marker
    dangling = []     # Marker auf fehlende Quelle
    weak = []         # Marker mit zu geringem Token-Overlap

    sentences = [s.strip() for s in _SENT_SPLIT.split(answer or "") if s.strip()]
    for sent in sentences:
        ids = marker_re.findall(sent)
        # nur Saetze mit echtem Inhalt zaehlen (Ueberschriften/Fragmente lockerer)
        has_content = len(_tokens(sent)) >= 3
        if not ids:
            if has_content:
                ungrounded.append(sent)
            continue
        for cid in ids:
            if cid not in sources:
                dangling.append({"marker": cid, "sentence": sent})
                continue
            if min_overlap > 0.0:
                st = _tokens(sent) - {c.lower() for c in ids}
                src_t = _tokens(sources[cid])
                if st:
                    overlap = len(st & src_t) / len(st)
                    if overlap < min_overlap:
                        weak.append({"marker": cid, "overlap": round(overlap, 3),
                                     "sentence": sent})

    ok = not (ungrounded or dangling or weak)
    return {
        "grounded": ok,
        "sentences_total": len(sentences),
        "ungrounded_sentences": ungrounded,
        "dangling_markers": dangling,
        "weak_support": weak,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prueft Quellen-Grounding einer Antwort.")
    ap.add_argument("--answer", required=True, help="Datei mit dem Antworttext")
    ap.add_argument("--sources", required=True, help="JSON-Datei: {id: snippet}")
    ap.add_argument("--marker", default=r"\[(\w+)\]",
                    help=r"Regex fuer Zitat-Marker, Gruppe 1 = Quellen-ID (Default [\w])")
    ap.add_argument("--min-overlap", type=float, default=0.0,
                    help="Minimaler Token-Overlap Satz<->Quelle (0 = aus)")
    ap.add_argument("--strict", action="store_true", help="Exit 10 bei Maengeln")
    args = ap.parse_args(argv)

    with open(args.answer, "r", encoding="utf-8", errors="ignore") as fh:
        answer = fh.read()
    with open(args.sources, "r", encoding="utf-8", errors="ignore") as fh:
        sources = json.load(fh)

    report = check(answer, sources, marker=args.marker, min_overlap=args.min_overlap)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and not report["grounded"]:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
