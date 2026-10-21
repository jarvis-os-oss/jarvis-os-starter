# cron-meta-guard (opt-in plugin)

A cron job that runs an agent sometimes answers with a meta reply instead of the
deliverable ("I stand ready", "if you like, I can send it", "I need explicit
approval"). In a scheduled run nobody can answer, so that text would be
delivered to the end user as the message. This plugin stops that.

Ships as a plugin directory (`plugins/cron-meta-guard/`). It is inactive until
the operator lists it in `plugins.enabled` of a profile. No upstream patch, no
profile overwrite, stdlib only.

## Flow

1. The hook `transform_llm_output` fires per agent turn. If the agent runs inside
   a cron execution and the final text matches the meta rules below, the hook
   replaces it with `[SILENT]`. The scheduler then does not deliver (the output
   stays stored locally).
2. A daemon thread waits until the run has finished, then
   - marks the job `last_status=error` (visible in a cron monitor),
   - attempt 1: restarts the job once through `trigger_job` with the extra
     instruction "output ONLY the message text",
   - attempt 2 (retry failed as well): no delivery to the end user, an entry in
     the alert file for the operator, no further retry.
3. A clean run resets the per-job counter. Counter state expires after 6 hours.

## When a text counts as a meta reply

The built-in patterns are German phrases (for example "ich stehe bereit",
"falls du moechtest", "explizite Freigabe", "soll ich"). Add your own
language by extending `PATTERNS` and `OPENING_PATTERNS` in `__init__.py`.

Only texts up to 1500 characters are checked (`CRON_META_GUARD_MAX_LEN`), so long
reports are never swallowed. A short text is judged only if (a) its first
sentence is a clarifying question or meta opening, or (b) at least two different
patterns appear. A single "soll ich" inside the running text of a briefing stays
clean.

## Allowlist

Jobs listed in `plugins/cron-meta-guard/allowlist.json` (field `entries`: job id,
`profile:job_id` or job name, glob allowed) and in the env var
`CRON_META_GUARD_ALLOWLIST` (comma list) are not checked at all. Script jobs
(`no_agent`) are detected at runtime and skipped as well. The file ships with an
empty list.

## Configuration (all optional)

| Variable | Meaning |
| --- | --- |
| `CRON_META_GUARD_DISABLE=1` | Kill switch, the hook passes everything through |
| `CRON_META_GUARD_MAX_LEN` | Length limit in characters (default 1500) |
| `CRON_META_GUARD_ALLOWLIST` | Extra allowlist entries, comma separated |
| `CRON_META_GUARD_ALLOWLIST_FILE` | Alternative allowlist file |
| `CRON_META_GUARD_LOG` | JSONL log (default `$HERMES_HOME/logs/cron_meta_guard.log`, never contains the reply text) |
| `CRON_META_GUARD_STATE` | Retry counter file |
| `CRON_META_GUARD_ALERT` | Operator alert file |

## Enable

1. Add `cron-meta-guard` to `plugins.enabled` of the profiles that run
   agent cron jobs.
2. Restart the gateway of those profiles.
3. Trigger one agent cron job and check the log file.

## Limits

- Only agent jobs are affected. `no_agent` jobs have no LLM text.
- The job status is set after the run ends. Shortly before that, a monitor still
  shows the previous status.
- The pattern list is a heuristic. A meta reply that neither opens with a
  clarifying question nor contains two patterns is not detected (by design, to
  avoid false alarms).
- Not verified live in this kit: a real scheduler run with the plugin loaded.
  The unit tests cover the logic with stubs, plus one test against the real
  `cron.jobs` store when the Hermes package is importable (skipped otherwise).

## Tests

```
python3 -m unittest tests.test_cron_meta_guard -v
```
