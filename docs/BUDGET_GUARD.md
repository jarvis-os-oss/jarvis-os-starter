# LLM-Budget-Guard

`scripts/budget_guard.py` prueft geschaetzte LLM-Ausgaben pro Agent und fuer die
ganze Flotte gegen konfigurierte Limits. Ergaenzt das tiered-model-routing (das
Kosten senkt) um die Kontroll-Seite.

## Warum
Kostenkontrolle: erkennt, wenn ein Agent oder die Flotte das Budget im
aktuellen Fenster ueberschreitet.

## Wichtig
Der Guard DROSSELT nichts von selbst (kein Auto-Eingriff in fremde Agenten). Er
liefert ein Urteil (Exit 1 = ueber Limit), das der Betreiber oder sein
Security-Agent auswertet.

## Eingaben
- Config `scripts/budget_guard.json` (ships DISABLED): `fleet_limit`,
  `default_agent_limit`, `agent_limits`, `warn_ratio`.
- Usage-JSON provider-agnostisch: `{"spend": {"agent": kosten}}` oder eine
  Liste `[{"agent": ..., "cost": ...}]`. Wie diese Datei entsteht, ist
  instanzspezifisch (z.B. aus `fleet_cost_report.py` oder Provider-Rechnungen).

## Aktivieren
1. `budget_guard.json` anpassen, `enabled: true` setzen, echte Limits eintragen.
2. `python3 scripts/budget_guard.py --config scripts/budget_guard.json --usage <usage.json> --status-file <status.json>`

## Test
`python3 -m unittest tests.test_budget_guard -v`
