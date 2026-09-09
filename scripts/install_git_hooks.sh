#!/usr/bin/env bash
# Install the repo's git hooks (currently: the bot-identity pre-push guard).
#
# Two install modes:
#   default : copy scripts/hooks/* into .git/hooks/ (works everywhere)
#   --hookspath : set core.hooksPath = scripts/hooks (versioned hooks, git 2.9+)
#
# It also sets this repo's local git identity to the neutral bot, so ordinary
# commits carry the right metadata without the contributor having to remember.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_NAME="starter-kit-bot"
BOT_EMAIL="jarvis-os-oss@users.noreply.github.com"

cd "$ROOT"

# 1) Pin the bot identity locally (repo-scoped, does not touch global config).
git config user.name  "$BOT_NAME"
git config user.email "$BOT_EMAIL"
echo "[hooks] set local git identity: ${BOT_NAME} <${BOT_EMAIL}>"

# 2) Install the hook.
if [ "${1:-}" = "--hookspath" ]; then
  git config core.hooksPath scripts/hooks
  chmod +x scripts/hooks/* 2>/dev/null || true
  echo "[hooks] core.hooksPath -> scripts/hooks (versioned hooks active)"
else
  mkdir -p .git/hooks
  cp scripts/hooks/pre-push .git/hooks/pre-push
  chmod +x .git/hooks/pre-push
  echo "[hooks] installed .git/hooks/pre-push"
fi

echo "[hooks] Done. Pushes with a non-bot author/committer will now be rejected."
