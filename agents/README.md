# Team Charter

The default team shipped with the JARVIS-OS Starter Kit. JARVIS orchestrates,
the sub-agents specialise. All hand-offs go through JARVIS. Rename or replace
any agent by editing its `agents/<key>.SOUL.md` and the roster entry in
`dashboard/team_config.json`, or add a new one from `agents/_TEMPLATE.SOUL.md`.

| Key       | Name      | Role                          | Does                                                        |
|-----------|-----------|-------------------------------|------------------------------------------------------------|
| default   | JARVIS    | Chief of Staff / Orchestrator | Takes requests, routes to the team, bundles results back.  |
| assistant | Assistant | Admin / PA                    | Inbox triage, calendar, reminders, briefings.              |
| scout     | Scout     | Research / Intelligence       | Market and competitor research, comparisons, fact-checks.  |
| ada       | Ada       | Development                   | Builds tools and features on branches, opens PRs, no deploy.|
| scotty    | Scotty    | DevOps, Security & Maintenance| Infra, monitoring, updates, backups, reviews and deploys.  |
| pen       | Pen       | Content / Writing             | Drafts posts, articles, emails in the user's voice.        |

## Delegation model
1. JARVIS receives the request.
2. JARVIS routes each subtask to the fitting specialist.
3. Specialists work in isolation and report back to JARVIS.
4. JARVIS merges the results into one answer for the user.

## Boundary: Ada builds, Scotty operates
Ada writes code on `ada/*` branches and opens PRs. Scotty reviews, merges to
`main`, and deploys. The same instance must not both write code and sign off on
its security and stability. See `docs/BRANCH_PROTECTION.md`.

## Extending the team (Package 2)
Additional specialised roles (travel, shopping, style, health, finance, vehicle,
marketing, design, and more) are intentionally out of scope for this starter
kit. Add them later by dropping new SOUL files and roster entries. The
architecture is fully data-driven, so no code change is needed to add an agent.
