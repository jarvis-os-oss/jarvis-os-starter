# Before it runs unattended: the go-live checklist

You are about to leave a team of agents running with access to your terminal,
your files, your mail, and your calendar. Walk these five checks once before the
watchdog keeps the gateways up around the clock. They take a few minutes and
save the failure modes that actually bite first-time operators.

This is the multi-agent version of the single-agent "five checks" that circulate
in the Hermes community. The difference: you are not hardening one bot, you are
hardening JARVIS plus every sub-agent profile the watchdog starts.

## Five checks

### 1. Every agent restricts who may talk to it

Each Hermes profile that has a Telegram bot must set `TELEGRAM_ALLOWED_USERS` to
your own numeric Telegram ID (and only the IDs you trust). An empty allow-list
means anyone who finds the bot can drive an agent that reaches your terminal and
files. This kit runs one bot per agent (see the README), so check **every**
profile, not just JARVIS:

```bash
for p in default assistant scout ada scotty pen; do
  if [ "$p" = default ]; then f=~/.hermes/.env; else f=~/.hermes/profiles/$p/.env; fi
  printf '%-10s ' "$p"; grep -q '^TELEGRAM_ALLOWED_USERS=..*' "$f" 2>/dev/null \
    && echo "allow-list set" || echo "MISSING allow-list"
done
```

Set it **before** the first gateway start, never after. A bot that connects once
with an empty allow-list has already been reachable.

### 2. Secrets live in `.env`, nowhere else

API keys and bot tokens belong in `.env` files (the repo's root `.env` and each
`~/.hermes/profiles/<agent>/.env`), never in `config.yaml`, never in a
`SOUL.md`, never committed. The kit's secret gate enforces this on the repo:

```bash
python3 scripts/scan_secrets.py --all   # must exit 0
```

If a key ever lands in a tracked file, rotate it: assume it leaked the moment it
was committed.

### 3. The cockpit and the agent API server bind to loopback

The cockpit (`COCKPIT_PORT`, default 8517) and the Hermes API server
(`JARVIS_API_URL`, default `127.0.0.1:8642`) expose the full toolbox, terminal
included. Keep them on `127.0.0.1` unless you deliberately need remote access,
and when you do, put them behind TLS and an allow-list or a tunnel, never raw on
a public port. Confirm what is actually listening:

```bash
ss -tlnp | grep -E '8517|8642' || echo "nothing bound (expected before start)"
```

If the cockpit must be reachable, terminate TLS at a reverse proxy or a
Cloudflare tunnel and restrict the source, as `docs/HERMES_INSTALL.md` and the
README security section describe.

### 4. Draft always, send never (at least the first month)

Every agent's `SOUL.md` in this kit already carries "never send messages, spend
money, or make bookings without explicit approval." Leave that rule in place
while you learn what the team does. The moment you relax it is the moment a
half-finished reply reaches your best customer. Verify no profile has quietly
dropped the guardrail:

```bash
grep -L "without explicit approval\|never send" agents/*.SOUL.md
```

An empty result means every base agent still holds the line.

### 5. You know how to stop it

Before you rely on the team, know the off switch. Stop one gateway:

```bash
hermes -p <profile> gateway stop     # e.g. hermes -p default gateway stop
```

Stop the supervised set by not letting the watchdog restart them (remove or
pause its cron entry), and stop the cockpit with
`docker compose -f infra/docker-compose.yml down`. If you cannot name the stop
command from memory, you are not ready to leave it running.

## First diagnostic when something is off

If any check above looks wrong, or an agent behaves strangely, the first tool to
reach for is the Hermes self-test:

```bash
hermes doctor            # runtime, config, provider, and channel health
hermes -p <profile> doctor
```

It reports install, config, model, and channel problems in one place before you
start reading logs by hand.

## The one mistake that is not technical

The setup can be perfect and still fail if you never hand the team real work.
An agent that only ever sees test prompts learns nothing and gets quietly
abandoned. On day one, give it a task you would otherwise have done yourself,
and when an answer is wrong, add the missing fact to `memories/USER.md` instead
of re-phrasing the question.
