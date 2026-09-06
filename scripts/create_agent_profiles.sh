#!/usr/bin/env bash
# Create the base sub-agent Hermes profiles for a fresh JARVIS-OS install.
#
# `hermes setup` (or the starter kit's own onboarding) creates only the
# "default" profile, which is JARVIS itself. The team charter also names five
# sub-agents (assistant, scout, ada, scotty, pen). This script creates them
# non-interactively by cloning the already-configured "default" profile, so each
# new profile inherits the same provider, model, and API keys and needs NO extra
# interactive setup wizard.
#
# It is idempotent: profiles that already exist are left untouched.
#
# Usage:
#   scripts/create_agent_profiles.sh                 # creates the 5 defaults
#   AGENTS="assistant scout" scripts/create_agent_profiles.sh   # custom subset
#   HERMES_BIN=/usr/local/bin/hermes scripts/create_agent_profiles.sh
#
# After running, point the watchdog at them:
#   AIOS_AGENTS="default assistant scout ada scotty pen"   (in infra/.env)
set -u

: "${HERMES_BIN:=hermes}"
# Which sub-agent profiles to create. "default" is created by `hermes setup`,
# so it is intentionally NOT in this list.
: "${AGENTS:=assistant scout ada scotty pen}"
# Profile to clone provider/model/keys from. Must already be set up.
: "${CLONE_FROM:=default}"

if ! command -v "${HERMES_BIN}" >/dev/null 2>&1; then
  echo "ERROR: '${HERMES_BIN}' not found on PATH. Install Hermes first." >&2
  exit 1
fi

existing="$("${HERMES_BIN}" profile list 2>/dev/null || true)"
if [ -n "${existing}" ] && ! echo "${existing}" | grep -qw -- "${CLONE_FROM}"; then
  echo "ERROR: source profile '${CLONE_FROM}' does not exist. Run 'hermes setup' first." >&2
  exit 1
fi

created=""
skipped=""
for profile in ${AGENTS}; do
  if echo "${existing}" | grep -qw -- "${profile}"; then
    skipped="${skipped}${profile} "
    continue
  fi
  # </dev/null keeps this fully non-interactive. --clone-from copies
  # config.yaml, .env, SOUL.md and skills from the source profile.
  if "${HERMES_BIN}" profile create "${profile}" \
        --clone-from "${CLONE_FROM}" \
        --description "JARVIS-OS base sub-agent (${profile})" \
        </dev/null >/dev/null 2>&1; then
    created="${created}${profile} "
  else
    echo "WARN: failed to create profile '${profile}'" >&2
  fi
done

[ -n "${created}" ] && echo "Created: ${created}"
[ -n "${skipped}" ] && echo "Already existed (skipped): ${skipped}"

echo
echo "Next: wire the watchdog to these profiles by setting in infra/.env"
echo '  AIOS_AGENTS="default '"$(echo "${AGENTS}" | xargs)"'"'
echo
echo "NOTE: cloned profiles share default's SOUL.md (JARVIS). To give each a"
echo "distinct role, apply its charter soul file, e.g.:"
echo '  cp agents/scout.SOUL.md "$(hermes -p scout profile show 2>/dev/null | grep -i path | awk "{print \$NF}")/SOUL.md"'
echo "or edit \$HERMES_HOME/profiles/<name>/SOUL.md directly."
