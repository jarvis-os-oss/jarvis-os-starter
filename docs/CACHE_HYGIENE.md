# Cache-/Disk-Hygiene

`scripts/cache_hygiene.py` raeumt alte Cache-Dateien auf, bevor die Platte
volllaeuft. Toolchain-, Browser- und Modell-Caches wachsen still und kippen
sonst irgendwann Gateways und Backups.

## Warum
Verhindert Disk-Full-Ausfaelle durch periodisches, selektives Aufraeumen.

## Sicherheit
- DRY-RUN ist Default. Ohne `--apply` wird nur gelistet.
- Ships DISABLED: auch mit `--apply` wird ohne `enabled: true` nichts geloescht.
- Nur Dateien UNTERHALB eines konfigurierten `path` werden angefasst, Symlinks
  nie verfolgt, der `path` selbst nie geloescht.
- `min_age_days` schuetzt frische Dateien.

## Aktivieren
1. `scripts/cache_hygiene.json` anpassen (`REPLACE_WITH_CACHE_DIR` ersetzen).
2. Erst dry-run pruefen:
   `python3 scripts/cache_hygiene.py --config scripts/cache_hygiene.json`
3. `enabled: true` setzen, dann mit `--apply` scharf schalten (z.B. woechentlich
   per Cron).

## Test
`python3 -m unittest tests.test_cache_hygiene -v`
