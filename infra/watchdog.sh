#!/usr/bin/env bash
# JARVIS-OS watchdog. Ensures the cockpit dashboard and each configured agent
# gateway is running. Idempotent and safe to run repeatedly (e.g. from cron
# every few minutes). Prints one status line, silent when everything is healthy.
#
# LESSON BAKED IN: start gateways with `gateway run --replace`, NOT
# `gateway start`. `run --replace` cleanly takes over a stale/half-dead gateway
# instead of failing because "a gateway is already running", which is the
# failure mode that used to leave agents silently down after a crash-restart.
set -u

# --- config (override via environment or infra/.env) -------------------------
: "${AIOS_HOME:=/opt/aios}"
: "${COCKPIT_PORT:=8517}"
: "${COCKPIT_HEALTH_PATH:=/api/health}"
: "${PYTHON_BIN:=python3}"
: "${HERMES_BIN:=hermes}"
# Space-separated list of Hermes profiles to keep always-on. "default" = JARVIS.
# Ships with only "default" so a fresh install works out of the box. Create the
# five base sub-agents with scripts/create_agent_profiles.sh, then set
# AIOS_AGENTS (here or in infra/.env) to the profiles you actually created, e.g.
#   AIOS_AGENTS="default assistant scout ada scotty pen"
: "${AIOS_AGENTS:=default}"

DASH_LOG="${AIOS_HOME}/logs/dashboard.log"
mkdir -p "${AIOS_HOME}/logs" 2>/dev/null || true

started=""

# 1) Cockpit dashboard -------------------------------------------------------
if ! curl -s -o /dev/null --max-time 6 "http://127.0.0.1:${COCKPIT_PORT}${COCKPIT_HEALTH_PATH}"; then
  pkill -f "dashboard/app.py" 2>/dev/null
  sleep 1
  nohup "${PYTHON_BIN}" "${AIOS_HOME}/dashboard/app.py" > "${DASH_LOG}" 2>&1 &
  started="${started}dashboard "
  sleep 3
fi

# 2) Agent gateways ----------------------------------------------------------
# Preflight: the gateways run on the Hermes runtime, not in the cockpit
# container. If `hermes` is missing, every `gateway run` below fails and all
# agents stay STOPPED. Warn once with a pointer instead of spamming
# "hermes: command not found" into each gateway log, and skip the loop.
if ! command -v "${HERMES_BIN}" >/dev/null 2>&1; then
  echo "WARN: '${HERMES_BIN}' not found on PATH; skipping agent gateways." >&2
  echo "      Install the Hermes runtime on this host, then re-run:" >&2
  echo "        curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash" >&2
  echo "      Non-root installs land in ~/.local/bin; set HERMES_BIN to the" >&2
  echo "      absolute path if it is not on PATH. See docs/HERMES_INSTALL.md." >&2
else
# Snapshot the profiles that actually exist so we never spin up a doomed gateway
# for a profile that was never created (the watchdog would otherwise loop on it
# forever). A missing profile is reported once, not treated as a hard failure.
existing_profiles="$("${HERMES_BIN}" profile list 2>/dev/null || true)"
missing=""
for profile in ${AIOS_AGENTS}; do
  # Match the profile name as a whole word in `hermes profile list` output.
  if [ -n "${existing_profiles}" ] && ! echo "${existing_profiles}" | grep -qw -- "${profile}"; then
    missing="${missing}${profile} "
    continue
  fi
  if ! "${HERMES_BIN}" -p "${profile}" gateway status 2>/dev/null | grep -q "is running"; then
    # run --replace: idempotent takeover of any stale gateway for this profile.
    nohup "${HERMES_BIN}" -p "${profile}" gateway run --replace \
      > "${AIOS_HOME}/logs/gw_${profile}.log" 2>&1 &
    started="${started}${profile} "
    sleep 2
  fi
done
fi

if [ -n "${started}" ]; then
  echo "RESTARTED: ${started}"
fi
if [ -n "${missing:-}" ]; then
  echo "SKIPPED (profile not found, create it first): ${missing}"
fi
# silent when all OK (watchdog pattern)
