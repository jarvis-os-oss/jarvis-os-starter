#!/usr/bin/env python3
"""apply_routing.py -- reversible tiered model-routing applier for an AI-OS team.

Routes I/O-heavy grunt work (context compression, title generation, and
optionally sub-task delegation) to a cheap/fast model while keeping each agent's
main reasoning session on the frontier model. Hermes ships this capability
natively: per-task ``auxiliary`` model slots (compression, approval,
title_generation, ...) and a ``delegation.model`` override, each pinnable per
profile. So this tool builds NO custom LLM router. It reads ``routing.json`` and
drives the NATIVE ``hermes config set`` pipeline so each agent's grunt-work slots
point at the cheap tier while its main session stays on the frontier model.

Idea inspired by Spotify Engineering's "Portal cut my Claude Code token usage by
90%" (the ``shunt`` plugin). Spotify had to build PreToolUse hooks because Claude
Code has no first-class "cheap model for side-jobs" concept; Hermes does, so this
is a thin, reversible config applier over the native knobs instead of a hook
layer.

Note: a ``web_extract`` aux slot exists and is accepted as a valid name, but on
some Hermes versions the web_extract tool does deterministic truncate-and-store
with NO LLM call, so routing that slot is inert there. Verify with a live probe
before listing it in routing.json on your version.

Design goals:
- Additive + reversible: a master ``enabled`` flag (and per-agent ``enabled``)
  gates everything; ``--revert`` resets every routed slot back to ``auto`` and
  unsets ``delegation.model``. No irreversible edits.
- Respect the Hermes invariant "never hand-edit config.yaml": all changes go
  through ``hermes config set`` (subprocess), never a raw YAML write.
- Safe by default: dry-run prints the exact commands; nothing changes without
  ``--apply``.
- Safety guardrail: ``excluded_slots`` names slots that MUST stay on the
  frontier model for an agent (e.g. ``approval`` when it gates a real send /
  spend / booking). The applier RAISES if anything tries to route an excluded
  slot, turning the rule into a runtime invariant rather than a comment.

Stdlib only. Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "routing.json"

# Native Hermes auxiliary task slot names (see docs: configuring-models).
KNOWN_AUX_TASKS = {
    "vision", "compression", "web_extract", "approval", "title_generation",
    "skills_hub", "mcp", "triage_specifier", "kanban_decomposer",
    "profile_describer", "curator",
}


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _plan_for_agent(name: str, agent: dict, cfg: dict, revert: bool) -> list[list[str]]:
    """Return a list of `hermes config set/unset ...` argv lists for one agent."""
    cmds: list[list[str]] = []
    cheap = cfg["tiers"]["cheap"]
    aux_tasks = agent.get("auxiliary_tasks", cfg["defaults"]["auxiliary_tasks"])
    route_delegation = agent.get("delegation", cfg["defaults"]["delegation"])

    # Enforced exclusion guardrail (not just prose). ``excluded_slots`` names the
    # slots that MUST stay on the frontier model for this agent. If any routed
    # aux task, or delegation, collides with the exclusion, we fail loud rather
    # than silently routing a slot the operator declared off-limits. This turns
    # the "keep any send/spend/booking approval on the frontier model" rule into
    # a runtime invariant, not an ignorable comment.
    excluded = set(agent.get("excluded_slots", []))
    for slot in excluded:
        if slot not in KNOWN_AUX_TASKS and slot != "delegation":
            raise ValueError(
                f"agent {name!r}: unknown excluded slot {slot!r}")
    collide = excluded.intersection(aux_tasks)
    if collide:
        raise ValueError(
            f"agent {name!r}: slot(s) {sorted(collide)!r} are in both "
            f"auxiliary_tasks and excluded_slots (exclusion must win)")
    if "delegation" in excluded and route_delegation:
        raise ValueError(
            f"agent {name!r}: delegation is excluded but delegation=true")

    for task in aux_tasks:
        if task not in KNOWN_AUX_TASKS:
            raise ValueError(f"agent {name!r}: unknown auxiliary task {task!r}")
        if revert:
            # auto = use main model again
            cmds.append(["hermes", "config", "set", f"auxiliary.{task}.provider", "auto"])
            cmds.append(["hermes", "config", "set", f"auxiliary.{task}.model", ""])
        else:
            cmds.append(["hermes", "config", "set", f"auxiliary.{task}.provider", cheap["provider"]])
            cmds.append(["hermes", "config", "set", f"auxiliary.{task}.model", cheap["model"]])

    if route_delegation:
        if revert:
            cmds.append(["hermes", "config", "unset", "delegation.model"])
            cmds.append(["hermes", "config", "unset", "delegation.provider"])
        else:
            cmds.append(["hermes", "config", "set", "delegation.provider", cheap["provider"]])
            cmds.append(["hermes", "config", "set", "delegation.model", cheap["model"]])
    return cmds


def build_plan(cfg: dict, only: str | None, revert: bool) -> list[tuple[str, str, list[list[str]]]]:
    """Return [(agent_name, hermes_home, [argv, ...]), ...].

    When reverting we ignore the master/per-agent enabled flags so a disabled
    agent can still be cleaned up. When applying, both master and per-agent
    flags must be true.
    """
    plan: list[tuple[str, str, list[list[str]]]] = []
    master_on = bool(cfg.get("enabled", False))
    for name, agent in cfg.get("agents", {}).items():
        if name.startswith("_"):
            continue
        if only and name != only:
            continue
        if not revert:
            if not master_on or not agent.get("enabled", False):
                continue
        home = agent.get("hermes_home")
        if not home:
            raise ValueError(f"agent {name!r}: missing hermes_home")
        plan.append((name, home, _plan_for_agent(name, agent, cfg, revert)))
    return plan


def run(cfg: dict, only: str | None, revert: bool, apply: bool) -> int:
    plan = build_plan(cfg, only, revert)
    if not plan:
        action = "revert" if revert else "apply"
        print(f"[model-routing] nothing to {action} "
              f"(master enabled={cfg.get('enabled')}, check per-agent flags).")
        return 0

    verb = "REVERT" if revert else "APPLY"
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[model-routing] {verb} ({mode})  cheap-tier="
          f"{cfg['tiers']['cheap']['provider']}/{cfg['tiers']['cheap']['model']}")
    rc = 0
    for name, home, cmds in plan:
        print(f"\n# agent: {name}   HERMES_HOME={home}")
        for argv in cmds:
            printable = " ".join(argv)
            print(f"  HERMES_HOME={home} {printable}")
            if apply:
                env = dict(os.environ, HERMES_HOME=home)
                res = subprocess.run(argv, env=env, capture_output=True, text=True)
                if res.returncode != 0:
                    rc = res.returncode
                    print(f"    ! failed rc={res.returncode}: "
                          f"{(res.stderr or res.stdout).strip()[:200]}")
    if not apply:
        print("\n[model-routing] dry-run only. Re-run with --apply to execute. "
              "Requires the `hermes` CLI on PATH and write access to each HERMES_HOME.")
    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                   help=f"routing config JSON (default: {DEFAULT_CONFIG})")
    p.add_argument("--agent", default=None, help="limit to a single agent name")
    p.add_argument("--revert", action="store_true",
                   help="reset routed slots to auto / unset delegation model (reversal)")
    p.add_argument("--apply", action="store_true",
                   help="actually run `hermes config set` (default: dry-run)")
    args = p.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"error: config not found: {args.config}", file=sys.stderr)
        return 2
    try:
        return run(cfg, args.agent, args.revert, args.apply)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
