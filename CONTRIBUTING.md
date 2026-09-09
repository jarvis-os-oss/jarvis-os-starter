# Contributing to this repo

This is a **public** starter kit. Everything you push, including commit
**metadata**, is published. That means the author and committer name+email on
every commit must be neutral. This document is the rule that keeps real
identities out of the history.

## The one hard rule: commit as the bot, never as yourself

All commits in this repo use a single neutral identity:

```
name  = starter-kit-bot
email = jarvis-os-oss@users.noreply.github.com
```

Never commit with your personal name or email. A real address in commit
metadata is a PII leak even when the file contents are clean.

### Why this rule exists

The history was neutralised once before, then later PRs re-introduced real
author/committer emails because the contributor's local git identity was not the
bot and the bot config did not carry over to follow-up commits. This guard makes
that failure mode impossible to repeat silently.

## Set it up once (do this right after cloning)

```
bash scripts/install_git_hooks.sh
```

That command:
1. sets this repo's **local** git identity to the bot (does not touch your
   global git config, so your other repos are unaffected), and
2. installs a **pre-push hook** that rejects any push containing a commit whose
   author or committer is not the bot.

To use the versioned hook via `core.hooksPath` instead of copying it into
`.git/hooks`, run `bash scripts/install_git_hooks.sh --hookspath`.

## Committing to this repo

With the identity pinned (step 1 above), ordinary `git commit` already produces
bot-authored commits, so you normally do nothing extra.

If you somehow committed with the wrong identity, relabel before pushing:

```
# the last commit only
git commit --amend --reset-author --no-edit

# several commits: rebase and reset author, or re-run the full history
# normaliser used to purge the metadata (see scripts/ in the PII-purge tooling,
# git filter-repo with a name/email callback to the bot identity).
```

The pre-push hook will list any offending commit SHAs and refuse the push until
they are fixed. To bypass in an emergency (discouraged): `git push --no-verify`.

## CI enforcement

The secret/PII scanner (`scripts/scan_secrets.py`) runs in CI as a gate on file
content. The commit-identity rule is enforced locally by the pre-push hook; keep
it installed. Maintainers should also confirm, before merging a PR, that the PR
commits carry the bot identity (GitHub shows the author on each commit).
