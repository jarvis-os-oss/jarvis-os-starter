# Architecture

AI-OS is a small orchestrator-plus-specialists system. One coordinator
(the orchestrator) receives every request, routes work to specialised sub-agents, and
merges their results back into a single answer.

```
                 user
                  |
                  v
             +--------------+     each agent = one Hermes profile
             | orchestrator |            with its own SOUL.md (agents/*.SOUL.md)
             |  (default)   |
             +--------------+
              /  |   |   |  \
             v   v   v   v   v
      assistant researcher developer maintenance writer   (specialists)
             \   |   |   |   /
          report back to the orchestrator
```

## Components

- Agents (`agents/`): one `SOUL.md` per role. `orchestrator.SOUL.md` is the
  orchestrator. `_TEMPLATE.SOUL.md` is the blank for new agents. The roster in
  `dashboard/team_config.json` maps each agent key to a gateway port and UI
  metadata. Adding an agent is data-only: drop a SOUL file and a roster entry.

- Agent gateways: each agent runs as a Hermes profile exposing an OpenAI-style
  chat API on its own port. The cockpit and the orchestrator call these ports. Ports are
  declared per agent in the roster.

- Cockpit (`dashboard/`): a token-gated Flask app. `app.py` serves the UI and a
  small JSON API; `cockpit_team.py` is a data-driven blueprint that reads the
  roster and reports each gateway's live status. No LLM call is spent just to
  render status. Liveness has two sources, file-first with a TCP fallback:
    1. A host-written status file (`AIOS_STATUS_FILE`, default
       `/opt/aios/logs/agent_status.json`) produced by
       `dashboard/collect_status.py`. That collector reads each profile's
       authoritative `gateway_state.json` and confirms the pid is alive via
       `/proc`, so it reports true liveness even when the gateways expose no
       HTTP port. `dashboard/status_cron.sh` refreshes it on the host (cron).
       This is the reliable default for the headless starter kit. The file is
       trusted only while fresh (`AIOS_STATUS_MAX_AGE`, default 180s).
    2. A cheap TCP connect to the gateway port (legacy). Used only when the
       status file is missing, stale, or lacks a verdict for an agent. This
       keeps backward compatibility for deployments that DO expose the optional
       Hermes `api_server` on the roster ports.
  Why the TCP probe alone is not enough: by default the Hermes gateways run
  headless (`api_server` disabled), so nothing listens on the roster ports, and
  the cockpit is a container that cannot reach host loopback anyway. A pure TCP
  probe would therefore mark every healthy agent STOPPED.

- Infra (`infra/`): `watchdog.sh` keeps the cockpit and every configured
  gateway alive (idempotent, cron-friendly). `docker-compose.yml` + `Dockerfile`
  containerise the cockpit. Gateways run on the Hermes runtime and are managed
  by the watchdog, not modelled as compose services in the starter.

- Setup (`scripts/setup.py`): first-run onboarding. Generates `.env`, names your
  agents (the naming step), wires the `upstream` remote for updates.

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
- Build/deploy separation: the developer agent writes code on branches and opens
  PRs; the maintenance agent reviews, merges, and deploys. See
  `BRANCH_PROTECTION.md`.
