#!/usr/bin/env python3
"""Cache-/Disk-Hygiene: raeumt alte Cache-Dateien auf, bevor die Platte
volllaeuft.

Toolchain-, Browser- und Modell-Caches wachsen still und fuellen irgendwann
die Platte, was Gateways und Backups reihenweise kippt. Dieses Tool loescht
konfigurierte Cache-Pfade selektiv nach Alter und Muster.

SICHERHEIT:
  * DRY-RUN ist Default. Ohne --apply wird NUR gelistet, nie geloescht.
  * Ships DISABLED: ohne "enabled": true in der Config wird auch mit --apply
    nichts geloescht (Exit 0 mit Hinweis).
  * Nur Dateien UNTERHALB eines konfigurierten `path` werden angefasst.
    Symlinks werden nie verfolgt. Der `path` selbst wird nie geloescht.
  * `min_age_days` schuetzt frische Dateien (Default aus Config, sonst 7).

Config (siehe scripts/cache_hygiene.json):
  {
    "enabled": false,
    "targets": [
      {"path": "REPLACE_WITH_CACHE_DIR/toolchains", "glob": "*",
       "min_age_days": 30},
      {"path": "REPLACE_WITH_CACHE_DIR/browser", "glob": "*.tmp",
       "min_age_days": 7}
    ]
  }

Exit-Codes:
  0  ok (auch bei dry-run und wenn deaktiviert)
  2  Nutzungs-/Konfigurationsfehler
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
import time
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"[cache-hygiene {_now()}] {msg}", flush=True)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _iter_stale_files(base: str, pattern: str, min_age_s: float):
    """Yields (abs_path, size) fuer Dateien unter base, die aelter als
    min_age_s sind und pattern matchen. Symlinks werden ignoriert."""
    now = time.time()
    base = os.path.abspath(base)
    for root, dirs, names in os.walk(base):
        # Symlink-Verzeichnisse nicht betreten.
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for n in names:
            p = os.path.join(root, n)
            if os.path.islink(p):
                continue
            if not fnmatch.fnmatch(n, pattern):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            if (now - st.st_mtime) < min_age_s:
                continue
            yield p, st.st_size


def run(config: dict, apply: bool) -> int:
    default_age = int(config.get("min_age_days", 7))
    targets = config.get("targets", [])
    if apply and not config.get("enabled", False):
        _log("deaktiviert (enabled=false): --apply ignoriert, nur dry-run")
        apply = False
    total_files = 0
    total_bytes = 0
    for t in targets:
        base = t.get("path", "")
        if not base or not os.path.isdir(base):
            _log(f"uebersprungen (Pfad fehlt): {base}")
            continue
        pattern = t.get("glob", "*")
        min_age = int(t.get("min_age_days", default_age))
        min_age_s = min_age * 86400
        n_files = 0
        n_bytes = 0
        for p, size in _iter_stale_files(base, pattern, min_age_s):
            n_files += 1
            n_bytes += size
            if apply:
                try:
                    os.remove(p)
                except OSError as e:
                    _log(f"konnte nicht loeschen: {p} ({e})")
        total_files += n_files
        total_bytes += n_bytes
        verb = "geloescht" if apply else "wuerde loeschen"
        _log(f"{base} ({pattern}, >{min_age}d): {verb} {n_files} Dateien, "
             f"{n_bytes / 1_048_576:.1f} MiB")
    mode = "APPLY" if apply else "DRY-RUN"
    _log(f"{mode} gesamt: {total_files} Dateien, {total_bytes / 1_048_576:.1f} MiB")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cache-/Disk-Hygiene")
    ap.add_argument("--config", required=True, help="Pfad zur cache_hygiene.json")
    ap.add_argument("--apply", action="store_true",
                    help="tatsaechlich loeschen (Default: nur anzeigen)")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.config):
        _log(f"Config nicht gefunden: {args.config}")
        return 2
    try:
        config = load_config(args.config)
    except (json.JSONDecodeError, OSError) as e:
        _log(f"Config ungueltig: {e}")
        return 2
    return run(config, args.apply)


if __name__ == "__main__":
    sys.exit(main())
