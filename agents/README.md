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

## Keep each SOUL.md short

A `SOUL.md` is sent to the model on **every single turn**, so every character in
it is paid for on every response, forever. Keep souls lean: persona, tone, and
hard rules only. Anything longer (facts about the user, standing procedures)
belongs in `memories/USER.md`, `memories/MEMORY.md`, or a skill, not the soul.
The base souls here run roughly 1200 to 2000 characters; treat that as the
normal band and check any file with:

```bash
wc -c agents/*.SOUL.md
```

If one grows well past the others, move the excess into memory or a skill.

## Adding an agent by interview

You can write a new soul freehand from `_TEMPLATE.SOUL.md`, or let a Hermes chat
interview you and draft it. The structured interview forces a sharp scope and an
explicit list of what the agent must never do without approval. See
[`ONBOARDING_INTERVIEW.md`](ONBOARDING_INTERVIEW.md) for the copy-paste prompt.

## Delegation model
1. JARVIS receives the request.
2. JARVIS routes each subtask to the fitting specialist.
3. Specialists work in isolation and report back to JARVIS.
4. JARVIS merges the results into one answer for the user.

## Boundary: Ada builds, Scotty operates
Ada writes code on `ada/*` branches and opens PRs. Scotty reviews, merges to
`main`, and deploys. The same instance must not both write code and sign off on
its security and stability. See `docs/BRANCH_PROTECTION.md`.

## Optional agents (Package 2)
Additional specialised roles (travel, shopping, style-advisor, health-coach,
bookkeeping, finance-advisor, vehicle-manager, marketing-leadgen, design) ship as
optional, importable modules in [`optional/`](optional/). They are not part of
the base setup: import only the ones you need. Each has its own `SOUL.md` and an
import `README.md`. The architecture is fully data-driven, so adding one needs no
code change, just a soul file and a roster entry. See
[`optional/README.md`](optional/README.md) for the overview and per-module
instructions.
