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
