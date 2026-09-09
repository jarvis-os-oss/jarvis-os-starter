#!/usr/bin/env bash
# check_upstream_updates.sh -- READ-ONLY upstream update check for a kit instance.
#
# Tells the operator whether newer commits or a newer release tag exist on the
# upstream starter kit. It NEVER merges, pulls, resets, checks out, or writes to
# your working tree. It only runs `git fetch` (into remote-tracking refs and
# tags) and prints/logs a one-line verdict. Wire it into infra/watchdog.sh or a
# cron if you want a passive heads-up; acting on an update stays a deliberate,
# manual `git merge upstream/main` (see docs/UPSTREAM_UPDATES.md).
#
# Exit codes: 0 = up to date, 10 = updates available, 1 = could not check
# (offline / no upstream remote). Non-fatal by design: a failed check never
# breaks a watchdog run.
set -u

: "${UPSTREAM_REMOTE:=upstream}"
: "${UPSTREAM_BRANCH:=main}"
: "${AIOS_HOME:=$(cd "$(dirname "$0")/.." && pwd)}"
LOG="${UPDATE_CHECK_LOG:-${AIOS_HOME}/logs/upstream-check.log}"

log() {
  mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" | tee -a "$LOG" 2>/dev/null || echo "$1"
}

cd "$AIOS_HOME" 2>/dev/null || { log "UPSTREAM-CHECK: cannot cd to AIOS_HOME=$AIOS_HOME"; exit 1; }

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  log "UPSTREAM-CHECK: not a git repo at $AIOS_HOME; skipping"; exit 1
fi
if ! git remote get-url "$UPSTREAM_REMOTE" >/dev/null 2>&1; then
  log "UPSTREAM-CHECK: no '$UPSTREAM_REMOTE' remote; run scripts/setup.py or add it (see docs/UPSTREAM_UPDATES.md)"; exit 1
fi

# READ-ONLY fetch of the upstream branch + tags. No working-tree change.
if ! git fetch --quiet --tags "$UPSTREAM_REMOTE" "$UPSTREAM_BRANCH" 2>/dev/null; then
  log "UPSTREAM-CHECK: fetch from $UPSTREAM_REMOTE failed (offline?); skipping"; exit 1
fi

behind="$(git rev-list --count "HEAD..${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}" 2>/dev/null || echo '?')"
latest_tag="$(git tag -l --sort=-v:refname 'v*' | head -n1)"
have_tag="$(git describe --tags --abbrev=0 2>/dev/null || echo 'none')"

if [ "$behind" = "0" ]; then
  log "UPSTREAM-CHECK: up to date with ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} (latest release: ${latest_tag:-none})"
  exit 0
fi

msg="UPSTREAM-CHECK: ${behind} new upstream commit(s) on ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}."
if [ -n "$latest_tag" ] && [ "$latest_tag" != "$have_tag" ]; then
  msg="$msg Newer release ${latest_tag} available (you have ${have_tag})."
fi
msg="$msg Review then: git merge ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} (manual, see docs/UPSTREAM_UPDATES.md)."
log "$msg"
exit 10
