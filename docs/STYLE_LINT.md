# Konfigurierbares Style-/Policy-Lint-Gate

`scripts/style_lint.py` blockiert verbotene Zeichen oder Muster in Textdateien
(pre-commit oder CI). Die Regeln stehen komplett in einer Config-Datei, damit
jede Instanz ihre eigene Policy definiert.

## Warum
Ein generisches, konfigurierbares Gate fuer beliebige Stil- oder Policy-Regeln.
Als Beispiel-Regel ist ein Em/En/Figure-Dash-Verbot vordefiniert (eine
verbreitete Stil-Praeferenz), frei aenderbar oder ersetzbar.

## Regeltypen
- `substring`: literales Vorkommen (optional `ignore_case`).
- `regex`: Python-Regex.

## Aktivieren
1. `scripts/style_lint.json` anpassen, eigene Regeln definieren,
   `enabled: true` setzen.
2. Gegen konkrete Dateien (z.B. im Commit geaenderte):
   `python3 scripts/style_lint.py --config scripts/style_lint.json <datei> ...`
3. Oder ueber `include_globs`/`exclude_globs` das ganze Repo:
   `python3 scripts/style_lint.py --config scripts/style_lint.json --root .`

Ships DISABLED: ohne `enabled: true` blockiert nichts (Exit 0). Exit 1 = mind.
eine Verletzung.

## Test
`python3 -m unittest tests.test_style_lint -v`
