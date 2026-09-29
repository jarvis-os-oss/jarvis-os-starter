# Gateway-Health-Helfer

`scripts/gateway_health.py` prueft die Liveness der Agent-Gateways
file-first pro Profil. Die Gateways laufen headless (kein HTTP-Port), also ist
ein TCP-Connect kein verlaesslicher Test. Wahrheitsquelle ist die per-Profil-
Datei `gateway_state.json` (`gateway_state == "running"` plus eine `pid`, die
via `/proc` bestaetigt wird).

## Warum
Ergaenzt den Cockpit-Status-Collector um eine CLI fuer Ops und Monitoring, mit
derselben zuverlaessigen file-first Methode statt eines irrefuehrenden
Port-Checks.

## Subkommandos
- `status`: Tabelle RUNNING/STOPPED + pid.
- `json`: maschinenlesbarer Status.
- `check`: Exit 0 wenn alle erwarteten Profile laufen, sonst Exit 1.

## Nutzung
```
python3 scripts/gateway_health.py status
python3 scripts/gateway_health.py --profiles default,worker check
python3 scripts/gateway_health.py --hermes-home /path/.hermes json
```
Profile werden aus `dashboard/team_config.json` (Schluessel `key`) oder aus
`--profiles` gelesen, nicht hart codiert. Rein lesend: startet/stoppt nichts
(Neustart bleibt Sache des Watchdogs).

## Test
`python3 -m unittest tests.test_gateway_health -v`
