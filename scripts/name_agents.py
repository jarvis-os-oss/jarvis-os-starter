#!/usr/bin/env python3
"""AI-OS Starter Kit: agent naming step.

Give each agent its own name. This reads a names map (key -> display name),
then:
  1. fills the ``{{AGENT_NAME}}`` placeholder in each agent's persona file
     ``agents/<soul>.SOUL.md`` with the chosen name, and
  2. sets the matching ``name`` field in ``dashboard/team_config.json``.

Design goals:
- Standard library only, no dependencies.
- Idempotent and re-runnable: after the first run the persona files no longer
  contain ``{{AGENT_NAME}}``; a second run with a NEW name still updates both
  the roster ``name`` and the persona heading, because the applier also matches
  the previously-substituted name. Change a name in the map, re-run, done.
- Safe defaults: a missing or empty names file falls back to the generic role
  names already in the roster, so the kit works with zero configuration.

Names file format (see agents/names.example):
    <key> = <display name>        # inline comments after '#' are ignored
Blank lines and lines starting with '#' are ignored.

Usage:
    python3 scripts/name_agents.py                 # uses agents/names.local,
                                                   # falls back to names.example
    python3 scripts/name_agents.py --names PATH    # explicit names file
    python3 scripts/name_agents.py --check         # verify, write nothing
                                                   # (exit 1 if a placeholder
                                                   #  is still unresolved)
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(ROOT, "agents")
ROSTER_PATH = os.path.join(ROOT, "dashboard", "team_config.json")
NAMES_LOCAL = os.path.join(AGENTS_DIR, "names.local")
NAMES_EXAMPLE = os.path.join(AGENTS_DIR, "names.example")
PLACEHOLDER = "{{AGENT_NAME}}"
# Heading line in every SOUL: "# <name> (<Role>)". We rewrite the <name> part.
HEADING_RE = re.compile(r"^#\s+(.+?)\s+\((.*)\)\s*$")


def load_names(path):
    """Parse a '<key> = <name>' map. Returns {key: name}. Missing file -> {}."""
    names = {}
    if not path or not os.path.exists(path):
        return names
    with open(path) as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if key and val:
                names[key] = val
    return names


def resolve_names_file(explicit):
    if explicit:
        return explicit
    if os.path.exists(NAMES_LOCAL):
        return NAMES_LOCAL
    return NAMES_EXAMPLE


def _soul_path(agent):
    soul = agent.get("soul") or agent.get("key")
    return os.path.join(AGENTS_DIR, f"{soul}.SOUL.md")


def apply_to_soul(path, chosen, check=False):
    """Set the agent name in one SOUL file. Returns (changed, unresolved).

    - Replaces every literal {{AGENT_NAME}} with `chosen`.
    - Also rewrites the first heading's name part so a rename (from a prior
      concrete name to a new one) still lands. Persona body prose is untouched.
    `unresolved` is True if, after processing, a placeholder still remains
    (only possible in --check mode, where nothing is written).
    """
    if not os.path.exists(path):
        return (False, False)
    with open(path) as fh:
        text = fh.read()

    if check:
        return (False, PLACEHOLDER in text)

    new = text.replace(PLACEHOLDER, chosen)

    # Rewrite the first markdown heading "# <name> (<Role>)" -> chosen name,
    # so re-running with a different name updates the heading too.
    lines = new.split("\n")
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln)
        if m:
            lines[i] = f"# {chosen} ({m.group(2)})"
            break
    new = "\n".join(lines)

    # Rewrite the "You are **<x>**" self-reference on the first occurrence.
    new = re.sub(r"\*\*[^*]+\*\*", f"**{chosen}**", new, count=1)

    changed = new != text
    if changed:
        with open(path, "w") as fh:
            fh.write(new)
    return (changed, False)


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI-OS Starter Kit: name your agents")
    ap.add_argument("--names", default=None, help="path to the names map file")
    ap.add_argument("--check", action="store_true",
                    help="verify only, write nothing; exit 1 if a persona still "
                         "has an unresolved {{AGENT_NAME}} placeholder")
    args = ap.parse_args(argv)

    with open(ROSTER_PATH) as fh:
        roster = json.load(fh)
    agents = roster.get("agents", [])

    names_file = resolve_names_file(args.names)
    names = load_names(names_file)

    if args.check:
        unresolved = []
        for a in agents:
            _, un = apply_to_soul(_soul_path(a), a.get("name", ""), check=True)
            if un:
                unresolved.append(_soul_path(a))
        if unresolved:
            print("[name] unresolved {{AGENT_NAME}} placeholder in:")
            for p in unresolved:
                print(f"  {os.path.relpath(p, ROOT)}")
            return 1
        print("[name] all agent personas are named (no placeholder left).")
        return 0

    print(f"[name] using names file: {os.path.relpath(names_file, ROOT)}")
    roster_changed = False
    for a in agents:
        key = a.get("key")
        # chosen name: names-file entry > current roster name (role default)
        chosen = names.get(key, a.get("name", key))
        if a.get("name") != chosen:
            a["name"] = chosen
            roster_changed = True
        changed, _ = apply_to_soul(_soul_path(a), chosen)
        state = "updated" if changed else "unchanged"
        print(f"  {key:<12} -> {chosen:<16} ({state})")

    if roster_changed:
        with open(ROSTER_PATH, "w") as fh:
            json.dump(roster, fh, indent=2)
            fh.write("\n")
        print("[name] roster names updated.")
    else:
        print("[name] roster names already current.")
    print("[name] Done. Names applied to personas and roster.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
