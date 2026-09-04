# Bookkeeping agent (optional module)

Generic bookkeeping helper: records transactions, organises invoices and
receipts, reconciles accounts, and prepares clean data for an advisor.

## What it does
- Ongoing bookkeeping with strictly separate ledgers (personal / business).
- Invoice and receipt capture, categorisation, and filing.
- Account reconciliation and tidy exports for a tax advisor.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/bookkeeping/SOUL.md agents/bookkeeping.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` for `planned`):
   ```json
   {"key": "bookkeeping", "name": "Bookkeeping", "role": "Accounts & Records", "desc": "Transactions, invoices, receipts, reconciliation; prepares data for an advisor.", "port": 8651, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `bookkeeping` for its gateway.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Records and organises the past. Supplies numbers to the finance-advisor agent;
never moves money or files on the user's behalf without approval.
