# Upstream updates (one-way distribution)

New instances created from this starter kit stay current by pulling from THIS
repository as a git `upstream` remote. This is ordinary open-source style
distribution: one direction only, from the starter repo to the instance. There
is no runtime link, no callback, and no network access from the starter repo
into any instance. An instance pulls when its operator chooses to.

```
   jarvis-os-starter (this repo, the upstream)
          |
          |  git fetch upstream ; git merge upstream/main   (operator-initiated, one-way)
          v
   instance A     instance B     instance C     ...   (independent deployments)
```

## Wiring the upstream (once per instance)

`scripts/setup.py` does this for you, or do it manually:

```
git remote add upstream https://github.com/jarvis-os-oss/jarvis-os-starter.git
```

Set the correct URL with `--upstream` when running setup, or via the
`UPSTREAM_URL` environment variable.

## Pulling an update

```
git fetch upstream
git merge upstream/main        # or: git rebase upstream/main
# resolve any conflicts in files you customised (roster names, .env stays local)
docker compose -f infra/docker-compose.yml up -d --build   # redeploy
```

Your local `.env` is git-ignored, so an update never touches your secrets or
instance-specific values. Customisations you made to tracked files (for example
renamed agents in `dashboard/team_config.json`) may conflict on merge, resolve
them in favour of your local values.

## What the upstream never does

- It never connects to your instance.
- It never receives data from your instance.
- It carries no personal data, secrets, or instance-specific configuration.

It is a plain source repository you pull from, nothing more.

## Knowing when an update exists

There are two passive signals, both operator facing and both optional. Neither
ever reaches into your instance.

### 1. GitHub Releases and tags (primary)

Each meaningful state of this kit is cut as a GitHub Release with a semver tag
(`v0.1.0`, `v0.2.0`, ...). The release notes list what changed. Watch the repo
on GitHub (Watch -> Custom -> Releases) to get notified, or check
`https://github.com/jarvis-os-oss/jarvis-os-starter/releases`. A new release tag
is the clean "an update is available" marker.

### 2. Read-only update check (optional, opt-in)

`scripts/check_upstream_updates.sh` compares your instance against the upstream
without changing anything. It runs `git fetch` only and prints a one-line
verdict (how many upstream commits you are behind, and whether a newer release
tag exists). It NEVER pulls, merges, resets, or touches your working tree.

Run it by hand:

```
UPSTREAM_REMOTE=upstream bash scripts/check_upstream_updates.sh
# exit 0 = up to date, 10 = updates available, 1 = could not check
```

Or let the watchdog log it passively. It is OFF by default; enable it by setting
`AIOS_UPDATE_CHECK=1` (in your environment or `infra/.env`). The watchdog then
appends a verdict to `logs/upstream-check.log` on each run and stays silent
otherwise. Enabling the check never causes an automatic update, it only informs.

Acting on any signal is always a deliberate, manual step:

```
git fetch upstream
git merge upstream/main     # you decide, you resolve conflicts, you redeploy
```

## Where the updates come from (maintainer note)

This public kit is the PII-scrubbed, generic distribution of a larger private
codebase. Improvements flow one way, private to public, and only when they are
generic enough to help every kit user:

- A change in the private repo is marked portable by its author with a
  `Portable: yes` commit trailer (optionally `Portable-Scope: <paths>` to narrow
  which files are meant for the kit).
- A monthly helper collects those marked changes, runs a mandatory two-layer
  secret/PII scan on them (the kit's own `scripts/scan_secrets.py` plus an
  independent owner sweep), and opens ONE batched proposal pull request here.
- That PR is never auto-merged. A maintainer reviews it, genericizes any
  remaining specifics (agent names, paths, model IDs become kit placeholders),
  confirms behaviour-changing config ships disabled, then merges and cuts a
  release.

So every update you can pull has already passed a PII gate and human review
before it ever reached this public repo.
