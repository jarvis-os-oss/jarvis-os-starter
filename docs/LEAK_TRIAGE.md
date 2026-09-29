# Credential-Leak-Response

`scripts/leak_triage.py` erkennt in einem Text/Log/Notiz-Blob geleakte Secrets,
klassifiziert sie und gibt einen Sofortmassnahmen-Plan aus.

## Warum
Taucht ein Klartext-Secret in Daten, Notizen oder Logs auf, muss schnell klar
sein WAS geleakt ist und WAS zu tun ist (rotieren, widerrufen, Historie pruefen).

## Sicherheit
- Gibt Secrets NIE im Klartext aus, nur redigiert (erste/letzte Zeichen).
- Rein lesend, stdlib-only, kein Netzzugriff. Kein State, keine Aktivierung.

## Aktivieren / Einklinken
Auf verdaechtige Blobs anwenden (Logs, Notizen, Tool-Ausgaben):
```
python3 scripts/leak_triage.py --input notes.txt
cat some.log | python3 scripts/leak_triage.py --strict
```
`--strict` liefert Exit 10, wenn ein Secret gefunden wird. Der Report enthaelt
je Fund einen generischen Response-Schritt plus eine allgemeine Checkliste.

## Test
`python3 -m unittest tests.test_leak_triage -v`
