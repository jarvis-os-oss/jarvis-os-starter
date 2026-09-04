# Travel agent (optional module)

Generic travel planner: compares flights, hotels, and ground transport and
assembles an itinerary. Never books or pays without explicit approval.

## What it does
- Flight options (cheapest / fastest / recommended) with fare conditions.
- Accommodation matched to a travel profile.
- Ground logistics and a single approve-before-booking itinerary.

## How to import
This kit is fully data-driven, so adding an agent needs no code change.

1. Copy the soul file into the active agents folder:
   ```bash
   cp agents/optional/travel/SOUL.md agents/travel.SOUL.md
   ```
2. Add a roster entry to `dashboard/team_config.json` (pick a free port, or use
   `null` to show it as `planned` until deployed):
   ```json
   {"key": "travel", "name": "Travel", "role": "Travel Agent", "desc": "Flights, hotels, and trip logistics; books only on approval.", "port": 8643, "accent": "cyan"}
   ```
3. (Optional) Provision a Hermes profile named `travel` and let
   `infra/watchdog.sh` keep its gateway alive.

The cockpit and status probes pick the agent up from the roster automatically.

## Boundary
Prepares bookings and hands the go/no-go to the user through JARVIS. Never books
or pays on its own.
