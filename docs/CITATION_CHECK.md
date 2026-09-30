# Grounded-Citations

`scripts/citation_check.py` prueft, ob die Aussagen einer Antwort durch zitierte
Quellen gedeckt sind.

## Warum
Ein recherchierender Agent soll jede Sachaussage belegen. Das Tool findet
ungegroundete Saetze, Marker auf fehlende Quellen und (optional) zu schwachen
Overlap zwischen Aussage und Quelle.

## Sicherheit
- Rein lesend, deterministisch, stdlib-only. Kein State, keine Aktivierung.

## Aktivieren / Einklinken
Der eigene Recherche-/Compose-Schritt ruft das Tool auf dem erzeugten Text plus
Quellenliste auf:
```
python3 scripts/citation_check.py --answer answer.txt --sources sources.json
python3 scripts/citation_check.py --answer answer.txt --sources sources.json \
    --min-overlap 0.15 --strict
```
`sources.json`: `{"1": "quelltext ...", "2": "..."}`. Marker-Default ist `[n]`,
per `--marker` aenderbar. `--strict` gibt Exit 10 bei Maengeln.

## Test
`python3 -m unittest tests.test_citation_check -v`
