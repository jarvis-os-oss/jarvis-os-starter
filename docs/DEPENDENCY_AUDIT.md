# Dependency-Security-Audit

`scripts/dependency_audit.py` prueft ein Dependency-Manifest offline auf
Risikosignale, bevor eine fremde Abhaengigkeit adoptiert wird.

## Warum
Vor der Installation eines Drittanbieter-Pakets will man wissen: ungepinnte
Version, direkte VCS-/URL-Quelle, lokale Pfadquelle, gefaehrliche
Install-Hooks (package.json preinstall/postinstall/install).

## Sicherheit
- Installiert nichts, ruft kein Netz auf. Rein lesend, stdlib-only.
- Kein State, keine Aktivierung noetig.

## Aktivieren / Einklinken
Vor dem Adoptieren einer Dependency aufrufen, im CI oder von Hand:
```
python3 scripts/dependency_audit.py --manifest requirements.txt
python3 scripts/dependency_audit.py --manifest package.json --strict
```
`--strict` liefert Exit 10 bei mindestens einem HIGH-Risiko. Unterstuetzt
requirements.txt-Form und package.json.

## Grenze (ehrlich)
Rein statisch: prueft Manifest-Struktur, KEINE CVE-Datenbank-Abfrage (das
braeuchte Netz und eine Feed-Wahl). Fuer bekannte Schwachstellen zusaetzlich
ein Online-Advisory-Tool nutzen.

## Test
`python3 -m unittest tests.test_dependency_audit -v`
