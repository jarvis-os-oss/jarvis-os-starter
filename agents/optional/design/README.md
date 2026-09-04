# Design agent (optional module)

Generic design helper: brand and style guides, print and web layout proposals,
and visual assets. Technical build goes to the development agent.

## What it does
- Brand and style guide (colour, type, spacing, usage rules).
- Layout proposals for print and web, with mockups.
- Design specs and handoff notes for a developer.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/design/SOUL.md agents/design.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "design", "name": "Design", "role": "Brand & Visual Design", "desc": "Style guides, layouts, and assets; hands implementation to the dev agent.", "port": 8656, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `design` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Designs and specifies. Hands web and technical implementation to the development
agent (Ada) through JARVIS; never builds or deploys production code.
