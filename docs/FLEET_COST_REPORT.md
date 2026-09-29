# Fleet-Kostenreport

`scripts/fleet_cost_report.py` aggregiert geschaetzte LLM-Kosten pro Agent aus
einer oder mehreren Usage-JSON-Dateien und erzeugt einen Report pro Agent plus
Fleet-Summe. Reine Observability, aendert nichts.

## Warum
Ueberblick, welcher Agent wie viel kostet, als Basis fuer den Budget-Guard und
fuers Dashboard.

## Eingabeformate (tolerant)
- `{"records": [{"agent": ..., "cost": ...}, ...]}`
- Liste `[{"agent": ..., "cost": ...}, ...]`
- `{"spend": {"agent": kosten}}` (bereits aggregiert)

Kosten-Felder: `cost | spend | estimated_cost`. Agent-Felder:
`agent | name | profile`. Namensaufloesung roster-basiert
(`dashboard/team_config.json`), nicht hart codiert.

## Nutzung
```
python3 scripts/fleet_cost_report.py <usage.json | glob | verzeichnis> ...
python3 scripts/fleet_cost_report.py logs/usage --format json
```

## Test
`python3 -m unittest tests.test_fleet_cost_report -v`
