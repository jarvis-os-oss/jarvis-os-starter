#!/usr/bin/env python3
"""Cron-Kollisions- und Hygiene-Scanner.

Wenn viele Agenten viele Cronjobs haben, feuern schnell mehrere schwere Jobs
zur exakt selben Minute (typisch: alles auf "0 6 * * *"). Das erzeugt CPU-,
RAM- und API-Spitzen und verdeckt Fehler. Dieser Scanner liest eine oder
mehrere Hermes-Cron-jobs.json-Dateien und meldet:

  * KOLLISION: mehrere aktivierte Jobs mit identischem Schedule (Minute genau).
  * DICHTE:    Minuten mit mehr als `max_per_minute` gleichzeitigen Jobs.
  * HINWEIS:   Jobs ohne Schedule / deaktivierte Jobs (nur informativ).

Rein lesend. Aendert nie eine jobs.json. stdlib-only.

Erwartetes jobs.json-Schema (data-driven, tolerant):
  Entweder eine Liste von Job-Objekten oder ein Objekt mit Schluessel "jobs".
  Pro Job werden gelesen (alle optional):
    id / name        Bezeichner
    schedule / cron  5-Feld-Cron-Ausdruck ("m h dom mon dow")
    enabled          bool (Default true)

Exit-Codes:
  0  keine Kollision oberhalb der Schwelle
  1  mindestens eine Kollision / Ueberdichte gefunden
  2  Nutzungs-/Eingabefehler
"""
from __future__ import annotations

import argparse
import glob as globmod
import json
import os
import sys
from collections import defaultdict


def _log(msg: str) -> None:
    print(msg, flush=True)


def _load_jobs(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        jobs = data.get("jobs", [])
    elif isinstance(data, list):
        jobs = data
    else:
        jobs = []
    out = []
    for j in jobs:
        if isinstance(j, dict):
            out.append(j)
    return out


def _schedule_of(job: dict) -> str | None:
    for key in ("schedule", "cron", "cron_expression", "expr"):
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _label_of(job: dict) -> str:
    for key in ("name", "id", "job_id", "title"):
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "<unbenannt>"


def _is_enabled(job: dict) -> bool:
    val = job.get("enabled", True)
    return bool(val)


def scan(paths: list[str], max_per_minute: int) -> int:
    by_schedule: dict[str, list[str]] = defaultdict(list)
    disabled = 0
    no_sched = 0
    total = 0
    for path in paths:
        try:
            jobs = _load_jobs(path)
        except (json.JSONDecodeError, OSError) as e:
            _log(f"FEHLER beim Lesen von {path}: {e}")
            return 2
        origin = os.path.basename(os.path.dirname(os.path.abspath(path))) or path
        for job in jobs:
            total += 1
            if not _is_enabled(job):
                disabled += 1
                continue
            sched = _schedule_of(job)
            if not sched:
                no_sched += 1
                continue
            by_schedule[sched].append(f"{_label_of(job)} [{origin}]")

    findings = 0
    _log(f"Gescannt: {total} Jobs ({disabled} deaktiviert, {no_sched} ohne Schedule).")

    # Exakte Schedule-Kollisionen (mehr als 1 Job auf denselben Ausdruck).
    collisions = {s: labels for s, labels in by_schedule.items() if len(labels) > 1}
    if collisions:
        _log("\nKOLLISIONEN (identischer Schedule):")
        for sched in sorted(collisions):
            labels = collisions[sched]
            findings += 1
            _log(f"  '{sched}': {len(labels)} Jobs -> {', '.join(sorted(labels))}")

    # Ueberdichte: Schedules mit mehr Jobs als max_per_minute.
    dense = {s: labels for s, labels in by_schedule.items()
             if len(labels) > max_per_minute}
    if dense:
        _log(f"\nUEBERDICHTE (> {max_per_minute} Jobs auf einem Schedule):")
        for sched in sorted(dense):
            _log(f"  '{sched}': {len(dense[sched])} Jobs")

    if findings == 0:
        _log("\nOK: keine Schedule-Kollision gefunden.")
        return 0
    _log(f"\n{findings} kollidierende Schedule(s) gefunden. "
         f"Empfehlung: schwere Jobs ueber die Stunde verteilen.")
    return 1


def _expand_paths(inputs: list[str]) -> list[str]:
    paths: list[str] = []
    for inp in inputs:
        if os.path.isdir(inp):
            paths.extend(sorted(globmod.glob(os.path.join(inp, "**", "jobs.json"),
                                              recursive=True)))
        elif any(ch in inp for ch in "*?["):
            paths.extend(sorted(globmod.glob(inp, recursive=True)))
        else:
            paths.append(inp)
    return [p for p in paths if os.path.isfile(p)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cron-Kollisions- und Hygiene-Scanner")
    ap.add_argument("paths", nargs="+",
                    help="jobs.json-Dateien, Glob-Muster oder Verzeichnisse "
                         "(rekursiv nach jobs.json durchsucht)")
    ap.add_argument("--max-per-minute", type=int, default=1,
                    help="max. gleichzeitige Jobs pro Schedule ohne Warnung "
                         "(Default 1)")
    args = ap.parse_args(argv)
    paths = _expand_paths(args.paths)
    if not paths:
        _log("keine jobs.json gefunden")
        return 2
    return scan(paths, args.max_per_minute)


if __name__ == "__main__":
    sys.exit(main())
