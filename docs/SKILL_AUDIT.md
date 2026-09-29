# Skill-Library-Kuration

`scripts/skill_audit.py` inspiziert ein Skill-Verzeichnis und meldet Wildwuchs.
Es gibt NUR Vorschlaege aus, loescht oder splittet nie automatisch. Rein lesend.

## Warum
Jede skill-nutzende Instanz sammelt mit der Zeit doppelte, veraltete oder
uebergrosse Skills an. Der Audit macht das sichtbar.

## Befunde
- OVERSIZE: SKILL.md groesser als `--max-lines` (Split-Kandidat).
- DUP_NAME: mehrere Skills mit gleichem Namen.
- DUP_DESC: sehr aehnliche Beschreibungen (Schwelle `--desc-threshold`).
- STALE: seit `--stale-days` unveraendert (nur mit `--stale-days > 0`).
- NO_DESC: leere/fehlende description.

## Nutzung
```
python3 scripts/skill_audit.py <skill-root>
python3 scripts/skill_audit.py <skill-root> --max-lines 400 --stale-days 180 --format json
```
Exit 1 = mindestens ein Befund (informativ, Auswertung beim Betreiber).

## Test
`python3 -m unittest tests.test_skill_audit -v`
