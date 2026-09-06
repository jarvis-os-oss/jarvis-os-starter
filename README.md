# JARVIS-OS Starter Kit

A neutral, reusable starting point for building an AI operating system: one
orchestrator agent (JARVIS) that coordinates a team of specialised sub-agents,
plus a token-gated cockpit dashboard and the infrastructure to run it. No
personal data, no branding, no secrets. Fork it, name it, deploy it.

## What you get

- **JARVIS orchestrator** (`agents/jarvis.SOUL.md`): takes requests, routes to
  the team, merges results back.
- **5 base sub-agents** (generic templates):
  - **Assistant** (Admin / PA): inbox triage, calendar, reminders, briefings.
  - **Scout** (Research): market and competitor research, comparisons, fact-checks.
  - **Ada** (Development): builds tools and features on branches, opens PRs, never deploys.
  - **Scotty** (DevOps / Security): infra, monitoring, backups, reviews and deploys.
  - **Pen** (Content): drafts posts, articles, and emails in the user's voice.
- **Agent template** (`agents/_TEMPLATE.SOUL.md`) to add your own roles.
- **Cockpit dashboard** (`dashboard/`): token-gated Flask UI + API, data-driven
  agent roster with live status.
- **Infrastructure** (`infra/`): idempotent watchdog, Docker Compose, Dockerfile.
- **Onboarding** (`scripts/setup.py`): generates `.env`, renames agents, wires
  the upstream remote.
- **Security gate** (`scripts/scan_secrets.py` + CI): fails the build on any
  secret-shaped or denylisted token.

## Quick start

```bash
# 1. Clone your fork
git clone https://github.com/jarvis-os-oss/jarvis-os-starter.git
cd jarvis-os-starter

# 2. Run onboarding (generates .env, asks for the values you need)
python3 scripts/setup.py --upstream https://github.com/jarvis-os-oss/jarvis-os-starter.git

# 3. Review the generated .env (secrets are auto-generated, keys are placeholders)
#    Fill in your LLM provider key and any domain.

# 4. Build and run the cockpit
docker compose -f infra/docker-compose.yml up -d --build

# 5. Open the cockpit (token is the COCKPIT_TOKEN from your .env)
#    http://127.0.0.1:8517/?t=<COCKPIT_TOKEN>

# 6. Install the Hermes runtime the agent gateways run on (once, on the host).
#    Without this, the watchdog fails with "hermes: command not found".
#    See docs/HERMES_INSTALL.md for details and platform notes.
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hash -r && hermes --version

# 7. Create the base sub-agent profiles (non-interactive, clones "default").
#    One-off. Skip to run JARVIS-only for now (AIOS_AGENTS=default).
scripts/create_agent_profiles.sh
#    then set AIOS_AGENTS=default assistant scout ada scotty pen in .env

# 8. Start and supervise the agent gateways (run from cron every few minutes)
bash infra/watchdog.sh
```

The agent gateways run on the Hermes runtime (one profile per agent) and are
kept alive by `infra/watchdog.sh`. Hermes is a separate, free, open-source
runtime that you install on the host once; the kit does not bundle it. Install
it **before** the first watchdog run (step 6 above) or the watchdog aborts with
`hermes: command not found` and every agent stays `STOPPED`. See
[`docs/HERMES_INSTALL.md`](docs/HERMES_INSTALL.md) for the full install and a
`HERMES_BIN` note for non-root installs. Point the watchdog at your install with
the `AIOS_HOME` and `AIOS_AGENTS` environment variables and run it from cron.

## The setup script

`scripts/setup.py` is standard-library only and safe to re-run:

- Interactive by default: prompts for each `.env` value, Enter accepts the
  default. Auto-generates strong `COCKPIT_TOKEN` and `API_SERVER_KEY` so no
  placeholder secret is ever shipped.
- `--non-interactive`: fills everything from environment variables or defaults
  (CI-safe). Any value can be pre-set via an env var of the same name.
- Optionally renames agent display names in `dashboard/team_config.json`.
- Wires the `upstream` git remote (`--upstream <url>` or `UPSTREAM_URL`).
- `--force` to regenerate an existing `.env`.

## Updating from upstream

New instances stay current by pulling from this starter repo as a one-way git
`upstream`. There is no runtime link back to the source. See
[`docs/UPSTREAM_UPDATES.md`](docs/UPSTREAM_UPDATES.md).

```bash
git fetch upstream && git merge upstream/main
docker compose -f infra/docker-compose.yml up -d --build
```

## Customising the team

The system is data-driven. To add or change an agent:

1. Copy `agents/_TEMPLATE.SOUL.md` to `agents/<key>.SOUL.md` and fill it in.
2. Add a matching entry to `dashboard/team_config.json` (key, name, role, desc,
   port).

No code change is needed. The cockpit and status probes pick it up from the
roster.

## Creating the agent profiles

Each agent runs as its own Hermes profile. `hermes setup` (see step 6) creates
only the `default` profile, which is JARVIS itself. The five base sub-agents
(`assistant`, `scout`, `ada`, `scotty`, `pen`) are created separately. There is
no need to run the interactive setup wizard five more times:
`scripts/create_agent_profiles.sh` clones the already-configured `default`
profile, so every sub-agent inherits the same provider, model, and API key
non-interactively.

```bash
# Create all five base sub-agents (idempotent, skips any that already exist)
scripts/create_agent_profiles.sh

# Or a custom subset
AGENTS="assistant scout" scripts/create_agent_profiles.sh

# Verify
hermes profile list
```

Then widen the watchdog to the profiles you created, in `infra/.env`:

```
AIOS_AGENTS=default assistant scout ada scotty pen
```

The single generic command behind the script is:

```bash
hermes profile create <name> --clone-from default --description "<role>"
```

Cloned profiles share `default`'s SOUL.md (JARVIS). To give each a distinct
role, copy its charter soul file over the profile's `SOUL.md`, e.g.
`agents/scout.SOUL.md` -> the `scout` profile's `SOUL.md`.

Prefer JARVIS-only for now? Leave `AIOS_AGENTS=default`. The watchdog reports any
listed-but-missing profile once and keeps running instead of looping on it.

## Testing and CI

```bash
pip install -r dashboard/requirements.txt
python3 scripts/scan_secrets.py                 # secret / PII gate
python3 scripts/setup.py --non-interactive --skip-upstream --skip-rename --force
python3 -m unittest discover -s tests -v        # unit + cockpit smoke tests
```

CI (`.github/workflows/ci.yml`) runs the same three steps on every push and PR.

## Security and workflow

- Cockpit token-gated on every route except `/api/health`. Serve behind TLS.
- Secrets live in `.env` (git-ignored) and on the host, never in the repo.
- `main` is protected: changes land only via reviewed PRs. The agent that writes
  code (Ada) does not deploy it, the DevOps agent (Scotty) reviews and deploys.
  See [`docs/BRANCH_PROTECTION.md`](docs/BRANCH_PROTECTION.md).

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): components and data flow.
- [`docs/BRANCH_PROTECTION.md`](docs/BRANCH_PROTECTION.md): PR workflow and roles.
- [`docs/UPSTREAM_UPDATES.md`](docs/UPSTREAM_UPDATES.md): one-way update model.
- [`agents/README.md`](agents/README.md): the team charter.

## Optional agents (Package 2)

Nine additional specialised agent templates ship in `agents/optional/`. They are
NOT part of the base setup: import only the ones you need. Each is fully neutral
(generic roles, placeholder examples, no personal data) and needs no code change
to add, just a soul file and a roster entry in `dashboard/team_config.json`. See
[`agents/optional/README.md`](agents/optional/README.md) for the full guide and a
ready-to-paste roster snippet per module.

| Module              | Role                          | Does                                                             | How to import |
|---------------------|-------------------------------|-----------------------------------------------------------------|---------------|
| Travel              | Travel Agent                  | Flights, hotels, trip logistics; books only on approval.        | `cp agents/optional/travel/SOUL.md agents/travel.SOUL.md` + roster entry |
| Shopping            | Purchasing / Product Research | Product research and price comparison; buys only on approval.   | `cp agents/optional/shopping/SOUL.md agents/shopping.SOUL.md` + roster entry |
| Style Advisor       | Style / Fashion & Interior    | Style profile and criteria; hands buying to the shopping agent. | `cp agents/optional/style-advisor/SOUL.md agents/style-advisor.SOUL.md` + roster entry |
| Health Coach        | Habits & Wellbeing            | Habits and reminders; not medical advice.                       | `cp agents/optional/health-coach/SOUL.md agents/health-coach.SOUL.md` + roster entry |
| Bookkeeping         | Accounts & Records            | Transactions, invoices, receipts, reconciliation.               | `cp agents/optional/bookkeeping/SOUL.md agents/bookkeeping.SOUL.md` + roster entry |
| Finance Advisor     | Portfolio & Investment Review | Weighs options with pros and cons; no trades, no binding advice.| `cp agents/optional/finance-advisor/SOUL.md agents/finance-advisor.SOUL.md` + roster entry |
| Vehicle Manager     | Fleet & Maintenance           | Vehicle records, service reminders, specs, workshop prep.       | `cp agents/optional/vehicle-manager/SOUL.md agents/vehicle-manager.SOUL.md` + roster entry |
| Marketing Lead-Gen  | Campaigns & Lead Qualification| Campaign plans, draft outreach, lead scoring; sends on approval.| `cp agents/optional/marketing-leadgen/SOUL.md agents/marketing-leadgen.SOUL.md` + roster entry |
| Design              | Brand & Visual Design         | Style guides, layouts, assets; hands build to the dev agent.    | `cp agents/optional/design/SOUL.md agents/design.SOUL.md` + roster entry |

Each module's `README.md` carries the exact `team_config.json` snippet (with a
suggested free port) and the agent's boundary rules.
