# Memory-Snapshot-Backup

`scripts/memory_snapshot.py` erstellt versionierte, gepackte Snapshots der
Agent-Memory-Schicht und haelt eine Retention ein.

## Warum
Die Memory-Dateien eines Agenten (Notizen/Profil/Erinnerungen) sind wertvoll
und aendern sich staendig. Regelmaessige, zeitgestempelte Snapshots schuetzen
gegen Verlust und erlauben Rueckspielen.

## Sicherheit / ships disabled
- Ships DISABLED: ohne `"enabled": true` in `scripts/memory_snapshot.json` ist
  der Lauf ein No-Op (Exit 0, Hinweis).
- Schreibt NUR in den konfigurierten `dest`-Ordner. Quellen werden nur gelesen.
- Retention-Loeschung betrifft ausschliesslich eigene Snapshots (Praefix
  `memsnap-`) im `dest`-Ordner, nichts anderes. stdlib-only (tarfile).

## Aktivieren
1. `scripts/memory_snapshot.json` anpassen: `enabled: true`, `sources`
   (die eigenen Memory-Pfade, Platzhalter `REPLACE_WITH_PROFILE_HOME` ersetzen),
   `dest`, `retention_days`.
2. Laufen lassen (z.B. taeglich per Cron):
```
python3 scripts/memory_snapshot.py --config scripts/memory_snapshot.json
python3 scripts/memory_snapshot.py --config scripts/memory_snapshot.json --list
```

## Restore
Snapshot ist ein normales tar.gz: `tar xzf memsnap-<ts>.tar.gz -C <ziel>`. Ein
Backup ist nur real, wenn der Restore getestet wurde: regelmaessig probeweise in
einen Temp-Ordner entpacken und den Inhalt pruefen.

## Test
`python3 -m unittest tests.test_memory_snapshot -v`
