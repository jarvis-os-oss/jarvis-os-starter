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
: "${AIOS_AGENTS:=default assistant scout ada scotty pen}"

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
for profile in ${AIOS_AGENTS}; do
  if ! "${HERMES_BIN}" -p "${profile}" gateway status 2>/dev/null | grep -q "is running"; then
    # run --replace: idempotent takeover of any stale gateway for this profile.
    nohup "${HERMES_BIN}" -p "${profile}" gateway run --replace \
      > "${AIOS_HOME}/logs/gw_${profile}.log" 2>&1 &
    started="${started}${profile} "
    sleep 2
  fi
done

if [ -n "${started}" ]; then
  echo "RESTARTED: ${started}"
fi
# silent when all OK (watchdog pattern)
