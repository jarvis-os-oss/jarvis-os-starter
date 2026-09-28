# Starter-Kit Sync-Changelog

Nachvollziehbarkeits-Log des taeglichen Abgleichs gegen upstream main. Jeder Eintrag haelt fest, welche Upstream-Commits geprueft und wie sie klassifiziert wurden (auch wenn noch nicht umgesetzt). Erzeugt von scripts (Scotty), nicht manuell.

## 2026-09-28 - Sync-Lauf (upstream main 716a9b08d..e1c1e0edc)

Geprueft: 2 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 1.

- `7dd0fc044` squash merge PR #105: internal-bus escalation notify to JARVIS
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Generischer Infra-/Bugfix ('docker')
  - Dateien: evidence/rbac-destroy-class.evidence.json, ops_group/rbac.py, ops_group/tests/test_rbac.py
- `e1c1e0edc` feat(plugins): delegate-destroy-guard schliesst delegate_task-destroy-Luecke (#106)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Feature/Erweiterung ('feat(') - kein Muss fuers Kit
  - Dateien: evidence/delegate-destroy-guard.evidence.json, plugins/delegate-destroy-guard/README.md, plugins/delegate-destroy-guard/__init__.py, plugins/delegate-destroy-guard/plugin.yaml, plugins/delegate-destroy-guard/test_delegate_destroy_guard.py

Report an JARVIS: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall bei the operator/JARVIS)

## 2026-09-27 - Sync-Lauf (upstream main 9419a5019..716a9b08d)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

- `716a9b08d` squash merge PR #101: internal-bus escalation notify to JARVIS
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Generischer Infra-/Bugfix ('bump')
  - Dateien: docs/cron-jobs/skill-kurator.md, docs/skill-contract-format/CONTRACT.md, docs/skill-contract-format/test_skill_contract.py, docs/skill-contract-format/validate_contract.py, evidence/skill-versioning-staleness.evidence.json, skill-governance/METADATA_CONVENTION.md, skill-governance/skill_metadata.py, skill-governance/test_skill_metadata.py

Report an JARVIS: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall bei the operator/JARVIS)

## 2026-09-26 - Sync-Lauf (upstream main 600b5d112..9419a5019)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

- `9419a5019` docs(ops_group): Rollout-Plan v0.21.0 -> v0.21.5 (#100)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: the operator-spezifische Preference/Daten ('REDACTED')
  - Dateien: evidence/scotty-rollout-plan-v0215.evidence.json, ops_group/rollout_plan_v0215.md

Report an JARVIS: NEIN

## 2026-09-22 - Sync-Lauf (upstream main 10f8f06cd..600b5d112)

Geprueft: 3 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 3.

- `dc36bb1b0` docs(governance): MCP-Connector-Policy als interne Konvention (#81)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: docs/mcp-connector-policy.md, evidence/mcp-connector-policy.evidence.json
- `980531f2f` feat(skill): agent-architecture-audit als kanonische Skill-Quelle (#82)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Feature/Erweiterung ('feat(') - kein Muss fuers Kit
  - Dateien: evidence/agent-architecture-audit-skill.evidence.json, skills/agent-architecture-audit/SKILL.md, skills/agent-architecture-audit/scripts/architecture_audit.py, skills/agent-architecture-audit/scripts/test_architecture_audit.py
- `600b5d112` docs+tooling(skills): 'Use when'-Trigger-Konvention + Audit-Stamper (#83)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: docs/skill-use-when-convention.md, evidence/skill-use-when-triggers.evidence.json, scripts/apply_use_when_descriptions.py, scripts/skill_use_when_descriptions.json, scripts/test_apply_use_when_descriptions.py

Report an JARVIS: NEIN

## 2026-09-21 - Sync-Lauf (upstream main cab7755fa..10f8f06cd)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

- `10f8f06cd` secret_guard: Pre-Write Secret-Pattern-Warnung im Peer-Mesh-Bus (#97)
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('secret') - konservativ zur Pruefung markiert
  - Dateien: .gitignore, evidence/secret-guard.evidence.json, ops_group/README.md, ops_group/internal-bus.py, ops_group/internal-bus_cli.py, ops_group/secret_guard.py, ops_group/tests/test_internal-bus.py, ops_group/tests/test_secret_guard.py

Report an JARVIS: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall bei the operator/JARVIS)

## 2026-09-20 - Sync-Lauf (upstream main 3034f3b91..cab7755fa)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 1.

- `cab7755fa` AGENTS.md: kompakte Agent-Schnellreferenz im Repo-Root (#96)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: AGENTS.md, evidence/agents-md.evidence.json

Report an JARVIS: NEIN

## 2026-09-19 - Sync-Lauf (upstream main bb5dd9106..3034f3b91)

Geprueft: 1 neue Commits. Nachziehen: 1, bewusst nicht: 0, Entscheidung noetig: 0.

- `3034f3b91` squash merge PR #95: internal-bus escalation notify to JARVIS
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('security') - konservativ zur Pruefung markiert
  - Dateien: .gitignore, browser-profiles/README.md, browser-profiles/browser_profile.sh

Report an JARVIS: JA (1 Nachzieh-Kandidat(en) - Freigabe pro Fall bei the operator/JARVIS)

## 2026-09-18 - Sync-Lauf (upstream main 2dc1cd5d3..bb5dd9106)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

- `bb5dd9106` TEAM_INFO: Verifikation nicht als sichtbarer Meta-Satz (#94)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: the operator-spezifische Preference/Daten ('REDACTED')
  - Dateien: evidence/team-info-verification-fix.evidence.json, agents/TEAM_INFO.md, agents/ada.SOUL.md, agents/pixel.SOUL.md, agents/scotty.SOUL.md

Report an JARVIS: NEIN

## 2026-09-17 - Sync-Lauf (upstream main 93e647fd3..2dc1cd5d3)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 0, Entscheidung noetig: 1.

- `2dc1cd5d3` squash merge PR #93: internal-bus escalation notify to JARVIS
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: evidence/emilkowalski-design-skillset.evidence.json, scripts/apply_emilkowalski_skills.py, scripts/test_apply_emilkowalski_skills.py, skills/emilkowalski-design/LICENSE, skills/emilkowalski-design/README.md, skills/emilkowalski-design/animate-expo/RECIPES.md, skills/emilkowalski-design/animate-expo/SKILL.md, skills/emilkowalski-design/animate/RECIPES.md ...

Report an JARVIS: NEIN

## 2026-09-16 - Sync-Lauf (upstream main 3d81a091f..93e647fd3)

Geprueft: 1 neue Commits. Nachziehen: 0, bewusst nicht: 1, Entscheidung noetig: 0.

- `93e647fd3` squash merge PR #90: internal-bus escalation notify to JARVIS
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: the operator-spezifische Preference/Daten ('REDACTED')
  - Dateien: .github/workflows/ocr-precheck.yml, evidence/scotty-ocr-precheck-activate.evidence.json

Report an JARVIS: NEIN

## 2026-09-15 - Sync-Lauf (upstream main 4840a9809..3d81a091f)

Geprueft: 11 neue Commits. Nachziehen: 2, bewusst nicht: 2, Entscheidung noetig: 7.

- `3a6c3a413` Add Evidence Record convention for Ada PRs (#77)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: docs/evidence/README.md, docs/evidence/evidence.template.json, evidence/evidence-record-convention.evidence.json, scripts/test_validate_evidence.py, scripts/validate_evidence.py
- `35c8df717` ci(evidence-gate): validate_evidence.py als PR-Pflicht-Gate (#78)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: .github/workflows/evidence-gate.yml, evidence/ci-evidence-gate.evidence.json
- `4a705db4b` chore(scripts): add scotty reviewer_approve identity to gh_rest.py (#80)
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: the operator-spezifische Preference/Daten ('REDACTED')
  - Dateien: scripts/gh_rest.py
- `16c376ed7` squash merge PR #46: internal-bus escalation notify to JARVIS
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('pii') - konservativ zur Pruefung markiert
  - Dateien: internal-eval/.gitignore, internal-eval/README.md, internal-eval/agents.json, internal-eval/bridge.py, internal-eval/cases/ada.json, internal-eval/cases/donna.json, internal-eval/cases/agent-b.json, internal-eval/cases/agent-c.json ...
- `d154e3365` squash merge PR #53: internal-bus escalation notify to JARVIS
  - Verdikt: BEWUSST NICHT UEBERNEHMEN
  - Grund: the operator-spezifische Preference/Daten ('tts')
  - Dateien: docs/evals/codebase-memory-mcp.md
- `f752b72ec` squash merge PR #54: internal-bus escalation notify to JARVIS
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: docs/evals/agent-reach.md
- `085b4258c` squash merge PR #55: internal-bus escalation notify to JARVIS
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN
  - Grund: Security/Infra-Signal ('secret') - konservativ zur Pruefung markiert
  - Dateien: docs/evals/hermy-hq.md
- `d7930becd` [squash] PR #84: internal-bus escalation notify to JARVIS (T-005)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: evidence/scotty-model-correction.evidence.json, model-tiering/PER-TASK-PLAN.md, model-tiering/README.md, model-tiering/estimate_saving.py, model-tiering/test_apply_tiering.py, model-tiering/tiering.json
- `2af9f5b54` [squash] PR #85: internal-bus escalation notify to JARVIS (T-005)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: evidence/soul-separator-collapse.evidence.json, scripts/collapse_soul_separators.py, scripts/test_collapse_soul_separators.py
- `d7cd484ca` [squash] PR #86: internal-bus escalation notify to JARVIS (T-005)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Feature/Erweiterung ('pilot') - kein Muss fuers Kit
  - Dateien: evidence/agent-d-pilot-status.evidence.json, scripts/apply_magnet_pilot_status.py, scripts/test_apply_magnet_pilot_status.py
- `3d81a091f` [squash] PR #87: internal-bus escalation notify to JARVIS (T-005)
  - Verdikt: ADA/OWNER-ENTSCHEIDUNG NOETIG
  - Grund: Unklar - manuelle Einordnung noetig
  - Dateien: evidence/scout-fetch-skill.evidence.json, scout-fetch-protokoll/SKILL.md, scripts/apply_scout_fetch_skill.py, scripts/test_apply_scout_fetch_skill.py

Report an JARVIS: JA (2 Nachzieh-Kandidat(en) - Freigabe pro Fall bei the operator/JARVIS)

Dies ist eine neutrale Vorlage. Reale Eintraege entstehen erst zur Laufzeit in der jeweiligen Instanz und referenzieren dort ausschliesslich das lokal konfigurierte Upstream-Repo.

## Beispiel-Eintrag (Vorlage)

## JJJJ-MM-TT - Sync-Lauf (upstream main &lt;from-sha&gt;..&lt;to-sha&gt;)

Geprueft: N neue Commits. Nachziehen: a, bewusst nicht: b, Entscheidung noetig: c.

- `<commit-sha>` <commit-titel>
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN | BEWUSST NICHT UEBERNEHMEN | ENTSCHEIDUNG NOETIG
  - Grund: <generische Klassifikationsbegruendung, z.B. "Security/Infra-Signal", "generischer Bugfix", "Feature/Erweiterung - kein Muss fuers Kit">
  - Dateien: <betroffene Pfade>

Report an den Nutzer: JA/NEIN (Zahl der Nachzieh-Kandidaten - Freigabe pro Fall).
