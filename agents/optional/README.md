# Optional agents (Package 2)

These are additional, specialised agent templates that are NOT part of the base
setup. Import only the ones you need. Each lives in its own folder with a
`SOUL.md` (the agent persona) and a `README.md` (how to import it). They are
fully neutral: generic roles, placeholder examples, no personal data.

The base team ships in `agents/` (JARVIS plus five sub-agents). The kit is
data-driven, so importing an optional agent needs no code change, just a soul
file and a roster entry in `dashboard/team_config.json`.

## Available modules

| Folder              | Name               | Role                          | Does                                                              | Import |
|---------------------|--------------------|-------------------------------|-------------------------------------------------------------------|--------|
| `travel`            | Travel             | Travel Agent                  | Flights, hotels, trip logistics; books only on approval.          | [README](travel/README.md) |
| `shopping`          | Shopping           | Purchasing / Product Research | Product research and price comparison; buys only on approval.     | [README](shopping/README.md) |
| `style-advisor`     | Style Advisor      | Style / Fashion & Interior    | Style profile and criteria; hands buying to the shopping agent.   | [README](style-advisor/README.md) |
| `health-coach`      | Health Coach       | Habits & Wellbeing            | Habits and reminders; not medical advice.                         | [README](health-coach/README.md) |
| `bookkeeping`       | Bookkeeping        | Accounts & Records            | Transactions, invoices, receipts, reconciliation.                 | [README](bookkeeping/README.md) |
| `finance-advisor`   | Finance Advisor    | Portfolio & Investment Review | Weighs options with pros and cons; no trades, no binding advice.  | [README](finance-advisor/README.md) |
| `vehicle-manager`   | Vehicle Manager    | Fleet & Maintenance           | Vehicle records, service reminders, specs, workshop prep.         | [README](vehicle-manager/README.md) |
| `marketing-leadgen` | Marketing Lead-Gen | Campaigns & Lead Qualification| Campaign plans, draft outreach, lead scoring; sends on approval.  | [README](marketing-leadgen/README.md) |
| `design`            | Design             | Brand & Visual Design         | Style guides, layouts, assets; hands build to the dev agent.      | [README](design/README.md) |

## How to import one (summary)

1. Copy the soul file into the active agents folder, for example:
   ```bash
   cp agents/optional/travel/SOUL.md agents/travel.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (each module's README has a
   ready-to-paste JSON snippet with a suggested free port). Use `"port": null`
   to show the agent as `planned` until you deploy its gateway.
3. (Optional) Provision a Hermes profile of the same key and let
   `infra/watchdog.sh` keep its gateway alive.

The cockpit and status probes pick the agent up from the roster automatically.
No code change is required.

## Neutrality

Every template uses generic roles and placeholder examples only, with no names,
companies, or real data. The repo-wide secret / PII gate
(`scripts/scan_secrets.py`) runs over these files in CI like everything else.
