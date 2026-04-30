"""CLI sub-command: apply defaults to an env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.defaults import apply_defaults
from envoy.parser import parse_env_file, serialize_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_defaults(args: argparse.Namespace) -> int:
    """Apply KEY=VALUE defaults to an env file for any missing keys."""
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"Error: file not found: {env_path}", file=sys.stderr)
        return 1

    if not args.defaults:
        print("No defaults provided.", file=sys.stderr)
        return 1

    defaults: dict[str, str] = {}
    for item in args.defaults:
        if "=" not in item:
            print(f"Error: invalid default '{item}' — expected KEY=VALUE", file=sys.stderr)
            return 1
        k, _, v = item.partition("=")
        defaults[k.strip()] = v.strip()

    env = parse_env_file(str(env_path))
    result = apply_defaults(env, defaults)

    for entry in result.entries:
        from envoy.defaults import DefaultStatus
        if entry.status == DefaultStatus.APPLIED:
            print(_colored(str(entry), "32"))
        else:
            print(_colored(str(entry), "90"))

    if args.write:
        env_path.write_text(serialize_env(env))
        print(_colored(f"Written to {env_path}", "36"))

    print(result.summary())
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "defaults",
        help="Apply default values to missing keys in an env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "defaults",
        nargs="+",
        metavar="KEY=VALUE",
        help="Default key-value pairs to apply if missing",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Write changes back to the file",
    )
    p.set_defaults(func=cmd_defaults)
