# Team Charter

The default team shipped with the AI-OS Starter Kit. The orchestrator
coordinates, the sub-agents specialise. All hand-offs go through the
orchestrator. Agents ship with generic ROLE names; give each one your own name
in the naming step (`scripts/name_agents.py`, see `docs/GOING_LIVE.md`). Rename
or replace any agent by editing its `agents/<key>.SOUL.md` and the roster entry
in `dashboard/team_config.json`, or add a new one from
`agents/_TEMPLATE.SOUL.md`.

| Key         | Role name    | Role                          | Does                                                        |
|-------------|--------------|-------------------------------|-------------------------------------------------------------|
| default     | Orchestrator | Chief of Staff / Orchestrator | Takes requests, routes to the team, bundles results back.   |
| assistant   | Assistant    | Admin / PA                    | Inbox triage, calendar, reminders, briefings.               |
| researcher  | Researcher   | Research / Intelligence       | Market and competitor research, comparisons, fact-checks.   |
| developer   | Developer    | Development                   | Builds tools and features on branches, opens PRs, no deploy.|
| maintenance | Maintenance  | DevOps, Security & Maintenance| Infra, monitoring, updates, backups, reviews and deploys.   |
| writer      | Writer       | Content / Writing             | Drafts posts, articles, emails in the user's voice.         |

The "Role name" column is the default display name. It is a placeholder: pick
your own (e.g. call the orchestrator "Athena" or the developer "Ada") in the
naming step. The `Key` is the Hermes profile name and does not change.

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
1. The orchestrator receives the request.
2. The orchestrator routes each subtask to the fitting specialist.
3. Specialists work in isolation and report back to the orchestrator.
4. The orchestrator merges the results into one answer for the user.

## Boundary: the developer builds, the maintenance agent operates
The developer agent writes code on `dev/*` branches and opens PRs. The
maintenance agent reviews, merges to `main`, and deploys. The same instance must
not both write code and sign off on its security and stability. See
`docs/BRANCH_PROTECTION.md`.

## Optional agents (Package 2)
Additional specialised roles (travel, shopping, style-advisor, health-coach,
bookkeeping, finance-advisor, vehicle-manager, marketing-leadgen, design) ship as
optional, importable modules in [`optional/`](optional/). They are not part of
the base setup: import only the ones you need. Each has its own `SOUL.md` and an
import `README.md`. The architecture is fully data-driven, so adding one needs no
code change, just a soul file and a roster entry. See
[`optional/README.md`](optional/README.md) for the overview and per-module
instructions.
