#!/usr/bin/env bash
# Create the base sub-agent Hermes profiles for a fresh AI-OS install.
#
# `hermes setup` (or the starter kit's own onboarding) creates only the
# "default" profile, which is the orchestrator itself. The team charter also names five
# sub-agents (assistant, researcher, developer, maintenance, writer). This script
# creates them
# non-interactively by cloning the already-configured "default" profile, so each
# new profile inherits the same provider, model, and API keys and needs NO extra
# interactive setup wizard.
#
# IMPORTANT: cloning copies default's .env verbatim, which includes its
# TELEGRAM_BOT_TOKEN. Telegram lets only ONE gateway hold a given bot token at a
# time, so if every profile kept default's token they would all fight over the
# same bot: only one gateway stays RUNNING and the rest are silently taken over
# ("Telegram bot token was held by gateway PID X ... handoff completed") and end
# up STOPPED. To prevent that race, this script CLEARS TELEGRAM_BOT_TOKEN in
# every cloned profile so you are forced to give each sub-agent its OWN bot
# token (one bot per agent, created via @BotFather) before starting it.
#
# It is idempotent: profiles that already exist are left untouched.
#
# Usage:
#   scripts/create_agent_profiles.sh                 # creates the 5 defaults
#   AGENTS="assistant researcher" scripts/create_agent_profiles.sh   # custom subset
#   HERMES_BIN=/usr/local/bin/hermes scripts/create_agent_profiles.sh
#
# After running, give each profile its own bot token (see the closing notice),
# then point the watchdog at them:
#   AIOS_AGENTS="default assistant researcher developer maintenance writer"   (in infra/.env)
set -u

: "${HERMES_BIN:=hermes}"
# Which sub-agent profiles to create. "default" is created by `hermes setup`,
# so it is intentionally NOT in this list.
: "${AGENTS:=assistant researcher developer maintenance writer}"
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

# Resolve a profile's on-disk directory (its .env lives there) from
# `hermes profile show`, which prints a "Path:   <dir>" line.
profile_dir() {
  "${HERMES_BIN}" profile show "$1" 2>/dev/null \
    | awk -F': *' 'tolower($1) ~ /^path$/ {print $2; exit}' \
    | sed 's/[[:space:]]*$//'
}

# Remove the inherited Telegram bot token from a freshly cloned profile so it
# cannot race the source profile for the same bot. If a TELEGRAM_BOT_TOKEN line
# exists it is blanked (value cleared, kept as a labelled placeholder); if it is
# absent a commented placeholder is appended. Never prints the token value.
clear_telegram_token() {
  local dir env
  dir="$(profile_dir "$1")"
  if [ -z "${dir}" ]; then
    echo "WARN: could not resolve directory for profile '$1'; leave its TELEGRAM_BOT_TOKEN unset by hand" >&2
    return 0
  fi
  env="${dir}/.env"
  if [ ! -f "${env}" ]; then
    echo "WARN: no .env found for profile '$1' at ${env}; set its own TELEGRAM_BOT_TOKEN by hand" >&2
    return 0
  fi
  if grep -q '^[[:space:]]*TELEGRAM_BOT_TOKEN[[:space:]]*=' "${env}"; then
    # Blank the value in place (portable sed, works on GNU and BSD).
    sed -i.bak -E 's|^([[:space:]]*TELEGRAM_BOT_TOKEN[[:space:]]*=).*$|\1|' "${env}" \
      && rm -f "${env}.bak"
  else
    {
      echo ""
      echo "# One bot per agent: create a dedicated bot via @BotFather and put"
      echo "# its token here, or this profile will race others for the same bot."
      echo "TELEGRAM_BOT_TOKEN="
    } >> "${env}"
  fi
}

created=""
skipped=""
cleared=""
for profile in ${AGENTS}; do
  if echo "${existing}" | grep -qw -- "${profile}"; then
    skipped="${skipped}${profile} "
    continue
  fi
  # </dev/null keeps this fully non-interactive. --clone-from copies
  # config.yaml, .env, SOUL.md and skills from the source profile.
  if "${HERMES_BIN}" profile create "${profile}" \
        --clone-from "${CLONE_FROM}" \
        --description "AI-OS base sub-agent (${profile})" \
        </dev/null >/dev/null 2>&1; then
    created="${created}${profile} "
    clear_telegram_token "${profile}"
    cleared="${cleared}${profile} "
  else
    echo "WARN: failed to create profile '${profile}'" >&2
  fi
done

[ -n "${created}" ] && echo "Created: ${created}"
[ -n "${skipped}" ] && echo "Already existed (skipped): ${skipped}"

echo
echo "IMPORTANT: each new profile needs its OWN Telegram bot token."
echo "Telegram allows only ONE gateway to connect with a given bot token at a"
echo "time, so if the profiles share default's token they will all compete for"
echo "the same bot and only one stays RUNNING (the rest are taken over and end"
echo "up STOPPED). The inherited token has therefore been CLEARED in:"
echo "  ${cleared:-<none>}"
echo
echo "For EACH sub-agent, create a dedicated bot via @BotFather (/newbot, pick"
echo "any name) and paste its token into that profile's .env:"
for profile in ${AGENTS}; do
  echo "  ~/.hermes/profiles/${profile}/.env   ->   TELEGRAM_BOT_TOKEN=..."
done
echo
echo "Only AFTER every profile has its own token, wire the watchdog in infra/.env:"
echo '  AIOS_AGENTS="default '"$(echo "${AGENTS}" | xargs)"'"'
echo "then re-run: bash infra/watchdog.sh"
echo
echo "NOTE: cloned profiles share default's SOUL.md (the orchestrator). To give each a"
echo "distinct role, apply its charter soul file, e.g.:"
echo '  cp agents/researcher.SOUL.md "$(hermes -p researcher profile show 2>/dev/null | grep -i path | awk "{print \$NF}")/SOUL.md"'
echo "or edit \$HERMES_HOME/profiles/<name>/SOUL.md directly."
