# Marketing lead-gen agent (optional module)

Generic marketing helper: campaign planning, outreach drafting, and lead
qualification. Never sends into customer reach without approval.

## What it does
- Campaign planning (audiences, angles, channels, timing).
- Draft outreach and content for review.
- Lead qualification and pipeline summaries.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/marketing-leadgen/SOUL.md agents/marketing-leadgen.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "marketing-leadgen", "name": "Marketing Lead-Gen", "role": "Campaigns & Lead Qualification", "desc": "Campaign plans, draft outreach, lead scoring; sends only on approval.", "port": 8654, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `marketing-leadgen` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Prepares and drafts only. Nothing goes into customer reach without explicit
approval; respects consent and anti-spam rules.
