# Cron-Kollisions- und Hygiene-Scanner

`scripts/cron_collision_scan.py` liest eine oder mehrere Hermes-Cron-
`jobs.json`-Dateien und meldet Jobs, die zur exakt selben Minute feuern. So
lassen sich CPU-, RAM- und API-Spitzen durch gleichzeitige schwere Jobs
vermeiden.

## Warum
Bei vielen Agenten landen schnell mehrere schwere Jobs auf `0 6 * * *`. Der
Scanner macht solche Kollisionen sichtbar, bevor sie Last-Spitzen erzeugen.

## Befunde
- KOLLISION: mehrere aktivierte Jobs mit identischem Schedule.
- UEBERDICHTE: mehr als `--max-per-minute` Jobs auf einem Schedule.
- Deaktivierte / schedulelose Jobs werden nur gezaehlt.

## Nutzung
```
python3 scripts/cron_collision_scan.py <jobs.json | glob | verzeichnis> ...
python3 scripts/cron_collision_scan.py ~/.hermes --max-per-minute 1
```
Rein lesend. Exit 1 = mindestens eine Kollision gefunden.

## Test
`python3 -m unittest tests.test_cron_collision_scan -v`
