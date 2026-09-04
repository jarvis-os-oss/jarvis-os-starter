# Style advisor agent (optional module)

Generic style consultant for fashion and interiors: builds a style profile and
turns taste into selection criteria. Buys nothing itself.

## What it does
- Builds and maintains a style profile.
- Advises on outfits, wardrobe gaps, and interior choices.
- Produces handoff-ready selection criteria for a purchasing agent.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/style-advisor/SOUL.md agents/style-advisor.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "style-advisor", "name": "Style Advisor", "role": "Style / Fashion & Interior", "desc": "Style profile and selection criteria; hands buying to the shopping agent.", "port": 8649, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `style-advisor` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Advises and specifies criteria only. Hands sourcing and buying to the shopping
agent through JARVIS; never purchases.
