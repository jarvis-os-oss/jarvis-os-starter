# Product-/Price-Monitor

`scripts/price_monitor.py` verfolgt beobachtete Preise gegen Zielwerte und
alarmiert, wenn ein Ziel erreicht ist.

## Warum
Der Betreiber pflegt eine Watchlist (Name + Zielpreis) und will gemeldet
bekommen, wenn ein Preis das Ziel erreicht.

## Sicherheit / ships disabled
- Ships DISABLED: ohne `"enabled": true` in `scripts/price_monitor.json` ist der
  Lauf ein No-Op (Exit 0, Hinweis).
- KAUFT NICHTS und loest keine Bestellung aus. Meldet nur. stdlib-only.

## Grenze (ehrlich, wichtig)
Das Tool holt den aktuellen Preis NICHT selbst aus dem Netz. Das Abrufen ist
site-spezifisch (jede Seite anders, oft bot-geschuetzt) und absichtlich nicht
Teil dieses generischen Bausteins. Der Betreiber speist den aktuellen Preis ein
(`--price` oder `--snapshot`), z.B. aus einem eigenen Fetch-Schritt oder dem
Blocked-Page-Recovery-Baustein.

## Aktivieren
1. `scripts/price_monitor.json` anpassen: `enabled: true`, `state_file`-Pfad,
   `items` mit `name`+`target_price` setzen.
2. Preise einspeisen und bewerten:
```
python3 scripts/price_monitor.py --config scripts/price_monitor.json \
    --item widget --price 19.99
python3 scripts/price_monitor.py --config scripts/price_monitor.json \
    --snapshot prices.json
```
Exit 10 signalisiert mindestens ein erreichtes Ziel (fuer Alert-Gates/Cron).

## Test
`python3 -m unittest tests.test_price_monitor -v`
