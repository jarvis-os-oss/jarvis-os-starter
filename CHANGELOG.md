# Starter-Kit Sync-Changelog

Nachvollziehbarkeits-Log des taeglichen Abgleichs gegen upstream main. Jeder Eintrag haelt fest, welche Upstream-Commits geprueft und wie sie klassifiziert wurden (auch wenn noch nicht umgesetzt). Erzeugt von scripts (Scotty), nicht manuell.

## 2026-09-29 - Portabler Delta portiert (kuratierter Review-PR)

Ein kuratierter Batch generischer Verbesserungen wurde ins Kit portiert (ein Review-PR, kein Auto-Merge):

- state.db Guardian: scripts/state_guardian.py (stdlib-only integrity-check + Hot-Backup + Auto-Restore vor jedem Gateway-Start), tests/test_state_guardian.py (unittest), Watchdog-Verdrahtung in infra/watchdog.sh (AIOS_STATE_GUARD, default an, HERMES_HOME-basierte Profil-DB-Pfade), docs/STATE_GUARDIAN.md. Generischer Zuverlaessigkeits-Fix gegen die Reboot/OOM-Crash-Loop, trifft jede Kit-Instanz.

Bewusst NICHT portiert: instanzspezifische Persona-/Voice-Features, Team-/Rollen-Spezifika, interne Message-Bus-Details und rein interne Merge-Workflow-Fixes (nicht generisch genug fuers Kit).


## 2026-09-29 - Sync-Lauf (upstream main e1c1e0edc..c98f6d964)

Geprueft: 8 neue Commits. Nachziehen: 2, bewusst nicht: 5, Entscheidung noetig: 1.

Report an den Betreiber: JA (2 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

## 2026-09-28 - Sync-Lauf (upstream main 716a9b08d..e1c1e0edc)

Geprueft: 2 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 1.

Report an den Betreiber: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

## 2026-09-27 - Sync-Lauf (upstream main 9419a5019..716a9b08d)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

Report an den Betreiber: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

## 2026-09-26 - Sync-Lauf (upstream main 600b5d112..9419a5019)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

Report an den Betreiber: NEIN

## 2026-09-22 - Sync-Lauf (upstream main 10f8f06cd..600b5d112)

Geprueft: 3 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 3.

Report an den Betreiber: NEIN

## 2026-09-21 - Sync-Lauf (upstream main cab7755fa..10f8f06cd)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

Report an den Betreiber: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

## 2026-09-20 - Sync-Lauf (upstream main 3034f3b91..cab7755fa)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 1.

Report an den Betreiber: NEIN

## 2026-09-19 - Sync-Lauf (upstream main bb5dd9106..3034f3b91)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

Report an den Betreiber: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

## 2026-09-18 - Sync-Lauf (upstream main 2dc1cd5d3..bb5dd9106)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

Report an den Betreiber: NEIN

## 2026-09-17 - Sync-Lauf (upstream main 93e647fd3..2dc1cd5d3)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 1.

Report an den Betreiber: NEIN

## 2026-09-16 - Sync-Lauf (upstream main 3d81a091f..93e647fd3)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

Report an den Betreiber: NEIN

## 2026-09-15 - Sync-Lauf (upstream main 4840a9809..3d81a091f)

Geprueft: 11 neue Commits. Nachziehen: 2, bewusst nicht: 2, Entscheidung noetig: 7.

Report an den Betreiber: JA (2 Nachzieh-Kandidat(en) - Freigabe pro Fall beim Betreiber)

Dies ist eine neutrale Vorlage. Reale Eintraege entstehen erst zur Laufzeit in der jeweiligen Instanz und referenzieren dort ausschliesslich das lokal konfigurierte Upstream-Repo.

## Beispiel-Eintrag (Vorlage)

## JJJJ-MM-TT - Sync-Lauf (upstream main &lt;from-sha&gt;..&lt;to-sha&gt;)

Geprueft: N neue Commits. Nachziehen: a, bewusst nicht: b, Entscheidung noetig: c.

- `<commit-sha>` <commit-titel>
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN | BEWUSST NICHT UEBERNEHMEN | ENTSCHEIDUNG NOETIG
  - Grund: <generische Klassifikationsbegruendung, z.B. "Security/Infra-Signal", "generischer Bugfix", "Feature/Erweiterung - kein Muss fuers Kit">
  - Dateien: <betroffene Pfade>

Report an den Nutzer: JA/NEIN (Zahl der Nachzieh-Kandidaten - Freigabe pro Fall).
