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
git clone https://github.com/YOUR-ORG/jarvis-os-starter.git
cd jarvis-os-starter

# 2. Run onboarding (generates .env, asks for the values you need)
python3 scripts/setup.py --upstream https://github.com/YOUR-ORG/jarvis-os-starter.git

# 3. Review the generated .env (secrets are auto-generated, keys are placeholders)
#    Fill in your LLM provider key and any domain.

# 4. Build and run the cockpit
docker compose -f infra/docker-compose.yml up -d --build

# 5. Open the cockpit (token is the COCKPIT_TOKEN from your .env)
#    http://127.0.0.1:8517/?t=<COCKPIT_TOKEN>
```

The agent gateways run on the Hermes runtime (one profile per agent) and are
kept alive by `infra/watchdog.sh`. Point the watchdog at your install with the
`AIOS_HOME` and `AIOS_AGENTS` environment variables and run it from cron.

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

## Roadmap (Package 2, not included)

Additional specialised roles (travel, shopping, style, health, finance, vehicle,
marketing, design, and more) are intentionally out of scope for this starter
kit. They can be added later from the agent template with no code change.
