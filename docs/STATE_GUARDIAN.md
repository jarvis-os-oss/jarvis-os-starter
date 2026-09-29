# state.db Guardian (crash-restart-loop protection)

`scripts/state_guardian.py` closes a real availability gap: a hard abort (host
reboot, OOM kill, SIGKILL mid-write) can leave the Hermes `state.db` WAL
uncheckpointed and the database structurally corrupt. A naive watchdog then
blind-restarts the gateway, Hermes opens the corrupt DB, crashes, the watchdog
restarts again: a crash-restart loop that keeps agents down.

The guardian runs BEFORE each gateway start and:

- `check`   PRAGMA quick_check + integrity_check. Exit 0 healthy, 3 corrupt.
- `backup`  only if healthy: a consistent online hot-backup (`sqlite3` backup
            API, not `cp`) with rotation, after a clean WAL checkpoint.
- `guard`   check; on OK rotate a backup and exit 0 (start allowed). On
            corruption: no blind start, attempt auto-restore from the newest
            valid backup, re-check. Success exit 0, failure exit 3 (caller must
            abort the start and alert).
- `restore` manual restore from the newest (or a given) valid backup; the
            current state is preserved as `.corrupt-<ts>` first, never deleted.

Design: stdlib-only, idempotent, never destroys an original without first
saving a `.corrupt-<ts>` copy. Backups live in `<db-dir>/backups/` (keep 7 by
default, `--keep N`).

## Watchdog wiring

`infra/watchdog.sh` calls the guardian before every `gateway run`. It is on by
default (`AIOS_STATE_GUARD=1`) and safe: a missing DB (fresh install) or an
unknown DB path is never a false block, only a genuinely corrupt DB with no
valid backup blocks that one profile's start (reported as `BLOCKED: <profile>`).
Set `AIOS_STATE_GUARD=0` to disable, `HERMES_HOME` to point at a non-default
runtime home.

Manual use:

```
python3 scripts/state_guardian.py --db ~/.hermes/state.db check
python3 scripts/state_guardian.py --db ~/.hermes/state.db guard
python3 scripts/state_guardian.py --db ~/.hermes/state.db restore
```
