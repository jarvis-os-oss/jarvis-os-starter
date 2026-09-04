# Finance advisor agent (optional module)

Generic portfolio and investment reviewer: lays out options with balanced pros
and cons. Executes nothing and gives no binding advice.

> **Important:** This agent does NOT provide binding or regulated investment
> advice and never executes trades or moves money. Final decisions rest with the
> user, who should consult a licensed professional for regulated advice.

## What it does
- Portfolio overview and plain-language assessment.
- Options analysis with the case for and against, risks made explicit.
- Scenario framing as general information, using the bookkeeping numbers.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/finance-advisor/SOUL.md agents/finance-advisor.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "finance-advisor", "name": "Finance Advisor", "role": "Portfolio & Investment Review", "desc": "Weighs investment options with pros and cons; no trades, no binding advice.", "port": 8652, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `finance-advisor` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Evaluates and informs only. No trade, no transfer, no binding recommendation;
the user decides. Draws figures from the bookkeeping agent through JARVIS.
