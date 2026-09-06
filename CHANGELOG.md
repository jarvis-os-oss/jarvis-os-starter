# Starter-Kit Sync-Changelog

Nachvollziehbarkeits-Log des taeglichen Abgleichs gegen jarvis-ai-os main. Jeder Eintrag haelt fest, welche Upstream-Commits geprueft und wie sie klassifiziert wurden (auch wenn noch nicht umgesetzt). Erzeugt von scripts (Scotty), nicht manuell.

## 2026-09-06 - Sync-Lauf (jarvis-ai-os main 4e6a4a28b..e68689fdd)

Geprueft: 10 neue Commits. Nachziehen: 3, bewusst nicht: 5, Entscheidung noetig: 2.

- `48f5f06e5` fix(cockpit): Reaktor-Tap Voice + Mobile-Touch-Haertung (#29)
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('harden') - konservativ zur Pruefung markiert
  - Dateien: dashboard/index.html
- `f5d6e4a88` Add non-invasive server logging to cockpit voice turn path (#31)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: owner-spezifische Preference/Daten ('elevenlabs')
  - Dateien: dashboard/cockpit_voice.py
- `404b242d7` fix(cockpit): sync live voice fixes to repo (blob playback + echo-abort guard + notes-inbox) (#33)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: owner-spezifische Preference/Daten ('voice')
  - Dateien: dashboard/app.py, dashboard/index.html
- `2549b2bfa` sync(dashboard): notes-inbox dedup (sha256 title+content) + rate-limit 60->600 (#38)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: owner-spezifische Preference/Daten ('jarvis-os')
  - Dateien: dashboard/app.py
- `b398efff5` feat(handoff): Deadline-Zombies + Reap fuer verlorene Antworten (#25)
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Generischer Infra-/Bugfix ('timeout')
  - Dateien: handoff/README.md, handoff/board.py, handoff/cli.py, handoff/examples/delegate_with_board.py, handoff/tests/test_board.py, handoff/zombie_check.py
- `0db38f56d` feat(model-routing): rollout 2 tiered routing to Donna + Ledger (#34)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: owner-spezifische Preference/Daten ('donna')
  - Dateien: .gitignore, model-routing/README.md, model-routing/routing.json, model-routing/test_apply_routing.py
- `15b7190f4` feat(model-routing): rollout 3 tiered routing to Hunter (raw product data) (#35)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: owner-spezifische Preference/Daten ('donna')
  - Dateien: model-routing/README.md, model-routing/routing.json, model-routing/test_apply_routing.py
- `58917a029` security(cockpit): load PII lists from git-ignored config, not code (#39)
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('security') - konservativ zur Pruefung markiert
  - Dateien: .gitignore, dashboard/app.py, dashboard/pii_config.example.json
- `c11269f5c` Rollout 4: Flyaway tiered model-routing (#36)
  - Verdikt: ADA/owner-ENTSCHEIDUNG NOETIG
  - Grund: Feature/Erweiterung ('model-routing') - kein Muss fuers Kit
  - Dateien: model-routing/README.md, model-routing/routing.json, model-routing/test_apply_routing.py
- `e68689fdd` Rollout 5: Magnet tiered model-routing (#37)
  - Verdikt: ADA/owner-ENTSCHEIDUNG NOETIG
  - Grund: Feature/Erweiterung ('model-routing') - kein Muss fuers Kit
  - Dateien: model-routing/README.md, model-routing/apply_routing.py, model-routing/routing.json, model-routing/test_apply_routing.py

Report an JARVIS: JA (3 Nachzieh-Kandidat(en) - Freigabe pro Fall bei owner/JARVIS)

