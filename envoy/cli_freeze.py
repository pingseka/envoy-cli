"""CLI commands for freeze/lock functionality."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.freeze import FreezeStatus, check_frozen, freeze_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_freeze(args: argparse.Namespace) -> None:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: {env_path} not found.", file=sys.stderr)
        sys.exit(1)

    lockfile = Path(args.lockfile) if args.lockfile else None
    keys = args.keys if args.keys else None

    result = freeze_env(env_path, keys=keys, lockfile_path=lockfile)

    for entry in result.entries:
        if entry.status == FreezeStatus.LOCKED:
            print(_colored(f"  locked  {entry.key}", "32"))
        elif entry.status == FreezeStatus.ALREADY_LOCKED:
            print(_colored(f"  already {entry.key}", "33"))
        else:
            print(_colored(f"  skipped {entry.key}", "90"))

    print(f"\n{result.summary()}")
    print(f"Lockfile: {result.lockfile}")


def cmd_freeze_check(args: argparse.Namespace) -> None:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: {env_path} not found.", file=sys.stderr)
        sys.exit(1)

    lockfile = Path(args.lockfile) if args.lockfile else None
    violations = check_frozen(env_path, lockfile_path=lockfile)

    if not violations:
        print(_colored("No lockfile found or no locked keys.", "33"))
        sys.exit(0)

    all_ok = True
    for key, matches in violations.items():
        if matches:
            print(_colored(f"  ok      {key}", "32"))
        else:
            print(_colored(f"  CHANGED {key}", "31"))
            all_ok = False

    if not all_ok:
        print(_colored("\nFrozen value violations detected.", "31"), file=sys.stderr)
        sys.exit(1)
    else:
        print(_colored("\nAll frozen values intact.", "32"))


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_freeze = subparsers.add_parser("freeze", help="Lock env keys into a lockfile")
    p_freeze.add_argument("env_file", help="Path to .env file")
    p_freeze.add_argument("--lockfile", default=None, help="Path to lockfile (default: <env>.lock)")
    p_freeze.add_argument("keys", nargs="*", help="Keys to lock (default: all)")
    p_freeze.set_defaults(func=cmd_freeze)

    p_check = subparsers.add_parser("freeze-check", help="Verify frozen keys haven't changed")
    p_check.add_argument("env_file", help="Path to .env file")
    p_check.add_argument("--lockfile", default=None, help="Path to lockfile")
    p_check.set_defaults(func=cmd_freeze_check)
