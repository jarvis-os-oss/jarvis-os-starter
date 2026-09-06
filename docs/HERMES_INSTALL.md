# Installing the Hermes runtime

The JARVIS-OS cockpit (`infra/docker-compose.yml`) runs as a container, but the
**agent gateways do not**. Each agent is a [Hermes](https://github.com/NousResearch/hermes-agent)
profile, and `infra/watchdog.sh` starts and supervises those gateways by calling
the `hermes` command **on the host**. If `hermes` is not installed on the host,
the watchdog fails with:

```
infra/watchdog.sh: line NN: hermes: command not found
```

and every agent stays `STOPPED` in the cockpit. This is the single most common
first-run failure. Install the runtime **before** you run the watchdog
(`infra/watchdog.sh`) for the first time.

Hermes Agent is free and open source (MIT). It is **not** a private or bundled
dependency of this kit; you install it directly from the upstream project.

## Linux / macOS / WSL2 / Termux

```bash
# Debian/Ubuntu: the installer downloads Node.js as a .tar.xz, so xz-utils
# must be present first (git and curl are assumed already installed).
sudo apt install -y git curl xz-utils

# Official Hermes installer. Run it as the SAME user that will run the
# watchdog. As root it installs system-wide to /usr/local/bin/hermes;
# as a normal user it installs to ~/.local/bin/hermes.
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Refresh the current shell's command lookup, then verify.
hash -r
hermes --version
```

The installer pulls everything Hermes needs (uv, Python 3.11, Node.js, ripgrep,
ffmpeg); the only prerequisites you provide are `git`, `curl`, and (on Linux)
`xz-utils`. A headless server that does not need browser automation can skip the
Playwright/Chromium step:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser
```

## Windows (native, PowerShell)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

## Make `hermes` visible to the watchdog

`infra/watchdog.sh` invokes `hermes` by name, so the binary must be on the `PATH`
of whatever runs the watchdog (your shell, or the cron user).

- **Installed as root:** the binary lands at `/usr/local/bin/hermes`, already on
  the default `PATH`. Nothing more to do.
- **Installed as a normal user:** the binary lands at `~/.local/bin/hermes`.
  Minimal cron/systemd environments often omit `~/.local/bin`. Either add it to
  that user's profile, or point the watchdog at the absolute path with the
  `HERMES_BIN` environment variable:

  ```bash
  HERMES_BIN=/home/youruser/.local/bin/hermes bash infra/watchdog.sh
  ```

  `HERMES_BIN` is respected by both `infra/watchdog.sh` and
  `infra/gateway_up.sh`.

## Verify before running the watchdog

```bash
command -v hermes && hermes --version
```

If that prints a path and a version, the watchdog in the next step will find the
runtime. If it prints nothing, re-open your shell (`source ~/.bashrc`) or re-run
the installer; see the upstream
[FAQ](https://hermes-agent.nousresearch.com/docs/reference/faq) and
[installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
for `hermes: command not found` troubleshooting.
