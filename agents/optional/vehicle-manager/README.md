# Vehicle manager agent (optional module)

Generic vehicle helper: records, maintenance scheduling, specifications, and
workshop coordination.

## What it does
- Per-vehicle records and history.
- Inspection and service reminders before deadlines.
- Specifications on hand (oil grade, tyre size and pressure, intervals).
- Workshop appointment preparation.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/vehicle-manager/SOUL.md agents/vehicle-manager.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "vehicle-manager", "name": "Vehicle Manager", "role": "Fleet & Maintenance", "desc": "Vehicle records, service and inspection reminders, specs, workshop prep.", "port": 8653, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `vehicle-manager` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Tracks and reminds. Hands parts sourcing to the shopping agent and scheduling to
a calendar/PA agent; never buys or books without approval.
