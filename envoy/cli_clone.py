"""CLI command for cloning .env files."""

from __future__ import annotations

import sys
from typing import Dict

from envoy.clone import clone_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_clone(args) -> int:
    key_map: Dict[str, str] = {}
    if hasattr(args, "rename") and args.rename:
        for pair in args.rename:
            if "=" not in pair:
                print(
                    _colored(f"Invalid rename pair (expected OLD=NEW): {pair}", "31"),
                    file=sys.stderr,
                )
                return 2
            old, new = pair.split("=", 1)
            key_map[old.strip()] = new.strip()

    try:
        result = clone_env(
            source=args.source,
            destination=args.destination,
            prefix_filter=getattr(args, "prefix", None),
            key_map=key_map,
            strip_prefix=getattr(args, "strip_prefix", False),
        )
    except FileNotFoundError as exc:
        print(_colored(f"Error: {exc}", "31"), file=sys.stderr)
        return 1

    for entry in result.entries:
        if entry.status.value == "skipped":
            line = _colored(f"  SKIP     {entry.source_key}", "33")
        elif entry.status.value == "renamed":
            line = _colored(f"  RENAMED  {entry.source_key} -> {entry.dest_key}", "36")
        else:
            line = _colored(f"  COPIED   {entry.dest_key}", "32")
        print(line)

    print(_colored(result.summary(), "32"))
    return 0


def register_commands(subparsers) -> None:
    p = subparsers.add_parser("clone", help="Clone a .env file to a new destination")
    p.add_argument("source", help="Source .env file")
    p.add_argument("destination", help="Destination .env file")
    p.add_argument("--prefix", help="Only clone keys starting with this prefix")
    p.add_argument(
        "--strip-prefix",
        dest="strip_prefix",
        action="store_true",
        help="Strip the prefix from destination keys",
    )
    p.add_argument(
        "--rename",
        nargs="+",
        metavar="OLD=NEW",
        help="Rename keys during clone (e.g. FOO=BAR)",
    )
    p.set_defaults(func=cmd_clone)
