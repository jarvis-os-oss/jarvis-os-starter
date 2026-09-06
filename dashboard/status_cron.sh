#!/usr/bin/env bash
# JARVIS-OS cockpit status refresher (host-side cron helper).
#
# Runs dashboard/collect_status.py on the host and writes the sanitised
# agent_status.json into the cockpit's log volume, so the cockpit can report
# true gateway liveness without the gateways exposing an HTTP api_server port.
#
# WHY host-side: the authoritative Hermes state (gateway_state.json) and the
# live pids (/proc) exist on the HOST, not inside the cockpit container. The
# collector therefore has to run on the host and drop its result into the
# volume the cockpit already mounts.
#
# Install (every minute) with, e.g.:
#   printf '* * * * * %s/dashboard/status_cron.sh\n' "$PWD" | crontab -
# then verify with `crontab -l`.
#
# All paths are overridable via the environment so this stays generic. Defaults
# match the shipped docker-compose named volume (infra_aios_logs).
set -euo pipefail

# Directory of this script, so the cron entry can be a bare absolute path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Hermes home holding the per-profile gateway_state.json files.
export HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"

# Roster the collector reads (key -> port). Defaults to the shipped one.
export AIOS_ROSTER="${AIOS_ROSTER:-${SCRIPT_DIR}/team_config.json}"

# Where the cockpit container reads the status file. Default = host path of the
# infra_aios_logs docker volume mounted at /opt/aios/logs in the container.
export AIOS_STATUS_FILE="${AIOS_STATUS_FILE:-/var/lib/docker/volumes/infra_aios_logs/_data/agent_status.json}"

exec python3 "${SCRIPT_DIR}/collect_status.py"
