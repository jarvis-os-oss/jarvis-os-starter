# Tiered model-routing (optional, cost optimisation)

Route grunt-work turns (reading, summarizing, extracting, formatting raw text)
to a cheap/fast model and keep reasoning, decisions, and anything that can
authorize a side effect (send, spend, book) on the frontier model.

Idea inspired by Spotify Engineering's "Portal cut my Claude Code token usage by
90%" (the `shunt` plugin). Spotify had to build hooks because Claude Code has no
first-class "cheap model for side-jobs" concept. Hermes does, so this module is
a thin, reversible config applier over the native knobs instead of a hook layer.

## TL;DR

- No custom LLM router. The applier (`apply_routing.py`) reads `routing.json`
  and drives the native `hermes config set` pipeline to pin each agent's
  grunt-work slots to the cheap tier, while the agent's main reasoning session
  (`model.default`) stays on the frontier model and is never touched.
- Ships DISABLED (`"enabled": false`). You opt in deliberately, agent by agent.
- Fully reversible: master `enabled` flag, per-agent `enabled`, and
  `apply_routing.py --revert`.
- A reported ~90-95% cost saving on the routed grunt turns is typical for this
  pattern (large input, small output). Measure your own: compare $/turn for the
  same summarization task on your cheap vs frontier model before trusting a
  headline number.

## How Hermes makes this native

Two per-profile mechanisms cover the whole job, so no hook layer is needed:

1. **Auxiliary model slots** (`auxiliary.<task>` in `config.yaml`). Hermes
   offloads side-jobs (`compression`, `approval`, `title_generation`, `vision`,
   ...) to independently-configurable model slots, each defaulting to `auto`
   (= use the main model). Pinning one to a cheap model routes exactly that
   grunt work off the frontier model; the main tool-loop is untouched.
   Docs: /docs/user-guide/configuring-models
2. **`delegation.model`** -- all `delegate_task` children run on this cheaper
   model while the parent planner stays on the frontier model.
   Docs: /docs/user-guide/features/delegation

Both are per-profile, so each agent is tuned independently.

> NOTE on `web_extract`: a `web_extract` aux slot exists, but on some Hermes
> versions the `web_extract` tool does deterministic truncate-and-store with NO
> LLM call, so pinning that slot is inert there. Verify with a live probe before
> listing it in `routing.json` on your version. It is intentionally omitted from
> the shipped defaults.

## Files

| File | Purpose |
|---|---|
| `routing.json` | Policy: cheap/main tiers, per-agent opt-in, which aux slots + delegation to route, and per-agent `excluded_slots`. |
| `apply_routing.py` | Reads the policy, emits/executes native `hermes config set` per agent. Dry-run by default. Stdlib only. |

Unit tests live in the repo's top-level `tests/test_model_routing.py` (run by CI).

## Safety: the frontier line

Keep `approval` on the frontier model for any agent whose approval slot gates a
real side effect (sending mail, spending, booking). A cheap mis-score could
auto-approve something it should not. Likewise, an agent whose OUTPUT quality or
voice is the product (a public ghostwriter, a customer-outreach persona) should
not have its generative text routed cheap, even when no money or safety is at
stake: that is a reputation risk, treat it the same way.

This is enforced, not just documented. Declare the off-limits slots in
`excluded_slots` (e.g. `["approval", "delegation"]`). `apply_routing.py` RAISES
if anything ever tries to route an excluded slot, or turns on delegation while
it is excluded. The rule becomes a runtime invariant, not an ignorable comment.
And because routing only ever touches `auxiliary.*` and `delegation.*`, never
`model.default`, the deciding and text-generating path is structurally on the
frontier model: the config cannot accidentally move it.

## Configure

1. Set your two tiers in `routing.json` -> `tiers.cheap` / `tiers.main`
   (replace the `REPLACE_WITH_*` placeholders with your provider + model IDs).
2. For each agent you want to route: set `hermes_home` to that profile's real
   `HERMES_HOME` on your host, list the safe `auxiliary_tasks`, set
   `excluded_slots` for anything that must stay frontier, and flip its
   `enabled` to `true`.
3. Flip the master `enabled` to `true`.

## Apply / revert

```bash
# Dry-run (default): prints the exact native commands, changes nothing.
python3 model-routing/apply_routing.py --agent scout

# Apply one agent (needs the `hermes` CLI on PATH + write access to its HERMES_HOME).
python3 model-routing/apply_routing.py --agent scout --apply

# Roll back one agent instantly (resets slots to auto, unsets delegation model).
python3 model-routing/apply_routing.py --agent scout --revert --apply

# Kill switch for everything: set "enabled": false in routing.json (apply becomes a no-op),
# or run --revert without --agent to clean every listed agent.
python3 model-routing/apply_routing.py --revert --apply
```

## Suggested rollout

Pilot on a research/recon agent first (long sessions, heavy compression +
delegation, no side effects), watch one work cycle for quality regressions, then
extend to other agents' pure read/summarize slots. Keep every side-effecting
agent's `approval` slot, and every voice/taste agent's generative text, on the
frontier model.
