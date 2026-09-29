# Blocked-Page-Recovery

`scripts/block_detect.py` klassifiziert eine fehlgeschlagene Web-Antwort und
empfiehlt eine Recovery-Strategie.

## Warum
Ein Agent, der Webinhalte holt, laeuft regelmaessig in Sperren (403/429, WAF,
Bot-Wall, Captcha, Paywall). Statt blind zu wiederholen, klassifiziert dieses
Tool die Sperre und nennt die passende Gegenmassnahme.

## Sicherheit
- Holt selbst nichts aus dem Netz, aendert nichts. Rein lesend, stdlib-only.
- Kein State, keine Aktivierung noetig (on-demand Klassifikator).

## Aktivieren / Einklinken
Es gibt nichts zu aktivieren. Der eigene Fetch-Layer ruft das Tool nach einem
Fehlschlag auf und reagiert auf `kind`/`recovery`:
```
python3 scripts/block_detect.py --status 429 --body response.html
echo "<html>...</html>" | python3 scripts/block_detect.py --status 403 --strict
```
`--strict` liefert Exit 10, wenn die Antwort blockiert ist (fuer Automations-Gates).

## Test
`python3 -m unittest tests.test_block_detect -v`
