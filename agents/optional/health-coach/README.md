# Health coach agent (optional module)

Generic wellbeing helper: everyday habits, reminders, and preventive-appointment
tracking. Educational and organisational only.

> **Important:** This agent does NOT provide medical advice, diagnosis, or
> treatment and never replaces a qualified healthcare professional. For any
> clinical question, medication, or dosage, defer to a licensed clinician.

## What it does
- Daily-habit support (movement, sleep, hydration, nutrition routines).
- Neutral, discreet reminders for recurring health actions.
- Tracking of preventive check-up dates and general, sourced wellbeing info.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/health-coach/SOUL.md agents/health-coach.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "health-coach", "name": "Health Coach", "role": "Habits & Wellbeing", "desc": "Habit support and preventive-appointment tracking; not medical advice.", "port": 8650, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `health-coach` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
No diagnosis, medication, or treatment. Anything clinical is deferred to a
healthcare professional and escalated through JARVIS.
