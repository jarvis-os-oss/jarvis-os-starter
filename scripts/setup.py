#!/usr/bin/env python3
"""JARVIS-OS Starter Kit: first-run onboarding.

Generates a local ``.env`` from ``.env.example`` by asking for the values a new
instance needs (cockpit token, provider key, domain, optional agent renames),
and can wire the ``upstream`` git remote for one-way updates from this starter
repo.

Design goals:
- Standard library only, no dependencies.
- Idempotent and safe: never overwrites an existing ``.env`` without --force.
- Non-interactive friendly: any prompt can be pre-supplied via environment
  variables (e.g. ``COCKPIT_TOKEN=...``), and ``--non-interactive`` fills the
  rest with generated or placeholder values so CI can run it.
- Writes NO secrets into the repo: ``.env`` is git-ignored.
"""

import argparse
import json
import os
import re
import secrets
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_EXAMPLE = os.path.join(ROOT, ".env.example")
ENV_PATH = os.path.join(ROOT, ".env")
ROSTER_PATH = os.path.join(ROOT, "dashboard", "team_config.json")
DEFAULT_UPSTREAM = "https://github.com/YOUR-ORG/jarvis-os-starter.git"


def _parse_env_example(path):
    """Return [(key, default_value_or_comment_flag)] preserving order.

    Lines that are comments or blank are kept verbatim so the generated .env
    stays readable.
    """
    lines = []
    with open(path) as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
            if m:
                lines.append(("kv", m.group(1), m.group(2)))
            else:
                lines.append(("raw", line, None))
    return lines


def _prompt(key, default, interactive):
    """Resolve one value: env override > prompt (if interactive) > default."""
    if key in os.environ and os.environ[key].strip():
        return os.environ[key].strip()
    if not interactive:
        return default
    shown = default if default else "(empty)"
    try:
        got = input(f"  {key} [{shown}]: ").strip()
    except EOFError:
        got = ""
    return got or default


def _gen_token(nbytes=32):
    return secrets.token_urlsafe(nbytes)


# Keys that must never keep the placeholder value: auto-generate a strong one.
SECRET_KEYS = {"COCKPIT_TOKEN", "API_SERVER_KEY"}


def generate_env(interactive=True, force=False):
    if os.path.exists(ENV_PATH) and not force:
        print(f"[setup] .env already exists at {ENV_PATH} (use --force to overwrite). Skipping.")
        return False
    parsed = _parse_env_example(ENV_EXAMPLE)
    out = []
    print("[setup] Generating .env. Press Enter to accept the default.")
    for kind, a, b in parsed:
        if kind == "raw":
            out.append(a)
            continue
        key, default = a, b
        if key in SECRET_KEYS:
            # Never carry a placeholder secret forward; generate a fresh one
            # unless the operator supplied an override via env.
            default = os.environ.get(key, "").strip() or _gen_token()
            value = default if not interactive else _prompt(key, default, interactive)
        else:
            value = _prompt(key, default, interactive)
        out.append(f"{key}={value}")
    with open(ENV_PATH, "w") as fh:
        fh.write("\n".join(out) + "\n")
    os.chmod(ENV_PATH, 0o600)
    print(f"[setup] Wrote {ENV_PATH} (chmod 600). It is git-ignored, do not commit it.")
    return True


def rename_agents(interactive=True):
    """Optionally rename display names of agents in the roster."""
    if not interactive:
        return
    try:
        with open(ROSTER_PATH) as fh:
            data = json.load(fh)
    except Exception as e:
        print(f"[setup] could not read roster: {e}")
        return
    print("[setup] Rename agents? Press Enter to keep each name.")
    changed = False
    for a in data.get("agents", []):
        cur = a.get("name", "")
        try:
            got = input(f"  {a.get('key')} [{cur}]: ").strip()
        except EOFError:
            got = ""
        if got and got != cur:
            a["name"] = got
            changed = True
    if changed:
        with open(ROSTER_PATH, "w") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        print("[setup] Roster updated.")
    else:
        print("[setup] Roster unchanged.")


def wire_upstream(url):
    """Add (or update) the 'upstream' git remote for one-way pull updates."""
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("[setup] not a git repo, skipping upstream wiring.")
        return
    try:
        existing = subprocess.run(
            ["git", "-C", ROOT, "remote"], capture_output=True, text=True
        ).stdout.split()
        action = "set-url" if "upstream" in existing else "add"
        subprocess.run(["git", "-C", ROOT, "remote", action, "upstream", url], check=True)
        print(f"[setup] upstream remote {action}: {url}")
        print("[setup] Update later with: git fetch upstream && git merge upstream/main")
    except Exception as e:
        print(f"[setup] could not wire upstream: {e}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="JARVIS-OS Starter Kit setup")
    ap.add_argument("--non-interactive", action="store_true",
                    help="fill all values from env/defaults, no prompts (CI-safe)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing .env")
    ap.add_argument("--upstream", default=os.environ.get("UPSTREAM_URL", DEFAULT_UPSTREAM),
                    help="git URL of this starter repo for one-way updates")
    ap.add_argument("--skip-upstream", action="store_true", help="do not touch git remotes")
    ap.add_argument("--skip-rename", action="store_true", help="do not offer agent renames")
    args = ap.parse_args(argv)

    interactive = not args.non_interactive and sys.stdin.isatty()

    generate_env(interactive=interactive, force=args.force)
    if not args.skip_rename:
        rename_agents(interactive=interactive)
    if not args.skip_upstream:
        wire_upstream(args.upstream)
    print("[setup] Done. Next: review .env, then `docker compose -f infra/docker-compose.yml up -d --build`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
