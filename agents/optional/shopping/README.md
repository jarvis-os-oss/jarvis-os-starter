# Shopping agent (optional module)

Generic purchasing helper: product research, critical review reading, and price
comparison. Never buys without explicit approval and stays within budget.

## What it does
- Product research and side-by-side comparison against stated criteria.
- Critical review reading and price-history checks.
- A ranked shortlist with a clear recommendation.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/shopping/SOUL.md agents/shopping.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "shopping", "name": "Shopping", "role": "Purchasing / Product Research", "desc": "Product research and price comparison; buys only on approval, within budget.", "port": 8648, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `shopping` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Prepares the purchase and stops. The buy needs explicit approval and must stay
inside the agreed budget. For style-driven buys, criteria come from the
style-advisor agent.
