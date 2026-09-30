# PR-Security-Audit

`scripts/pr_security_audit.py` fuehrt einen statischen Pre-Merge-Scan eines
Unified-Diffs aus und meldet strukturierte JSON-Findings (keine Prosa).

## Warum
Vor dem Merge eines Agenten-PRs soll klar sein, ob der Diff riskante Muster auf
HINZUGEFUEGTEN Zeilen einfuehrt: Secret-shaped Tokens, eval/exec/os.system,
subprocess shell=True, deaktivierte TLS-Verifikation, pickle-Deserialisierung,
offene Permissions (777), neue Netz-Endpunkte.

## Sicherheit
- Betrachtet nur `+`-Zeilen, keine Kontext-/Minuszeilen. Rein lesend, stdlib-only.
- Kein State, keine Aktivierung noetig.

## Aktivieren / Einklinken
Im Review-/CI-Schritt auf den PR-Diff anwenden:
```
git diff origin/main...HEAD | python3 scripts/pr_security_audit.py --strict
python3 scripts/pr_security_audit.py --diff pr.diff
```
`--strict` liefert Exit 10 bei mindestens einem HIGH-Finding. Ausgabe ist ein
JSON mit `findings` (rule/level/file/line/message) und `summary`.

## Grenze (ehrlich)
Heuristisch/musterbasiert, kein vollstaendiger Dataflow. Fasst nur, was im Diff
sichtbar ist; ersetzt kein manuelles Review, engt es aber ein.

## Test
`python3 -m unittest tests.test_pr_security_audit -v`
