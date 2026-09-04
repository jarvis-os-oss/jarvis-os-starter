# Architecture

JARVIS-OS is a small orchestrator-plus-specialists system. One coordinator
(JARVIS) receives every request, routes work to specialised sub-agents, and
merges their results back into a single answer.

```
                 user
                  |
                  v
             +----------+          each agent = one Hermes profile
             |  JARVIS   |         with its own SOUL.md (agents/*.SOUL.md)
             | (default) |
             +----------+
              /  |   |  \
             v   v   v   v   v
      assistant scout ada scotty pen        (specialists)
             \   |   |   |   /
              report back to JARVIS
```

## Components

- Agents (`agents/`): one `SOUL.md` per role. `jarvis.SOUL.md` is the
  orchestrator. `_TEMPLATE.SOUL.md` is the blank for new agents. The roster in
  `dashboard/team_config.json` maps each agent key to a gateway port and UI
  metadata. Adding an agent is data-only: drop a SOUL file and a roster entry.

- Agent gateways: each agent runs as a Hermes profile exposing an OpenAI-style
  chat API on its own port. The cockpit and JARVIS call these ports. Ports are
  declared per agent in the roster.

- Cockpit (`dashboard/`): a token-gated Flask app. `app.py` serves the UI and a
  small JSON API; `cockpit_team.py` is a data-driven blueprint that reads the
  roster and reports each gateway's live status via a cheap TCP probe. No LLM
  call is spent just to render status.

- Infra (`infra/`): `watchdog.sh` keeps the cockpit and every configured
  gateway alive (idempotent, cron-friendly). `docker-compose.yml` + `Dockerfile`
  containerise the cockpit. Gateways run on the Hermes runtime and are managed
  by the watchdog, not modelled as compose services in the starter.

- Setup (`scripts/setup.py`): first-run onboarding. Generates `.env`, can rename
  agents, wires the `upstream` remote for updates.

## Key operational lesson baked in

Gateways are (re)started with `gateway run --replace`, never `gateway start`.
`run --replace` idempotently takes over a stale or half-dead gateway instead of
failing with "a gateway is already running", which is the failure mode that used
to leave agents silently down after a crash-restart. See `infra/watchdog.sh`.

## Security posture

- The cockpit is token-gated on every route except `/api/health`. Serve it only
  behind a reverse proxy or tunnel that terminates TLS.
- Secrets live in `.env` (git-ignored) and on the host, never in the repo.
  Config references them by name or path.
- `scripts/scan_secrets.py` runs in CI and fails the build on any secret-shaped
  or denylisted token, so nothing personal or credential-like can be committed.
- Build/deploy separation: the Dev agent (Ada) writes code on branches and opens
  PRs; the DevOps agent (Scotty) reviews, merges, and deploys. See
  `BRANCH_PROTECTION.md`.
