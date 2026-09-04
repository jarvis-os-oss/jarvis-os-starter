#!/usr/bin/env bash
# Start (or replace) a single agent gateway by Hermes profile.
# Usage: infra/gateway_up.sh <profile>
# Uses `gateway run --replace` so it is safe to re-run and cleanly takes over a
# stale gateway rather than erroring out.
set -euo pipefail

: "${AIOS_HOME:=/opt/aios}"
: "${HERMES_BIN:=hermes}"

profile="${1:-default}"
mkdir -p "${AIOS_HOME}/logs"
nohup "${HERMES_BIN}" -p "${profile}" gateway run --replace \
  > "${AIOS_HOME}/logs/gw_${profile}.log" 2>&1 &
echo "gateway up: ${profile} (pid $!)"
