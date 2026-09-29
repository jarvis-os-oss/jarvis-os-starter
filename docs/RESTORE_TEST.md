# Restore-Test fuer Backups

`scripts/restore_test.py` verifiziert, dass ein Backup sich tatsaechlich
zurueckspielen laesst. Ein Backup, das nie zurueckgespielt wurde, ist eine
Hoffnung, kein Backup. Das Tool spielt konfigurierte Quellen in ein
WEGWERF-Temp-Verzeichnis zurueck und prueft die Wiederherstellung. Produktive
Daten werden nie angefasst.

## Warum
Sichert die Wiederherstellbarkeit ab, nicht nur die Existenz eines Backups.

## Ziel-Typen
- `tarball`: extrahiert ein .tar/.tar.gz in ein Temp-Verzeichnis, prueft
  `min_files` und optionale `expect_members`.
- `sqlite`: kopiert das juengste Backup passend zu `glob` und prueft es mit
  `PRAGMA integrity_check`.

## Aktivieren
1. `scripts/restore_test.json` kopieren und anpassen.
2. `enabled` auf `true` setzen, `status_file` und Ziel-Pfade
   (`REPLACE_WITH_*` ersetzen) eintragen.
3. Aufruf: `python3 scripts/restore_test.py --config scripts/restore_test.json`
4. Optional woechentlich per Cron. Exit 1 = mindestens ein Ziel nicht
   wiederherstellbar (alarmieren).

Ships DISABLED: ohne `enabled: true` passiert nichts (Exit 0).

## Test
`python3 -m unittest tests.test_restore_test -v`
