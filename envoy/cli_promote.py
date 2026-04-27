"""CLI commands for promoting env vars between environments."""
from __future__ import annotations

import sys
from typing import List, Optional

from envoy.promote import PromoteStatus, promote_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_promote(args) -> None:
    """Promote variables from source to target env file."""
    keys: Optional[List[str]] = args.keys if args.keys else None

    try:
        result = promote_env(
            source_path=args.source,
            target_path=args.target,
            keys=keys,
            overwrite=args.overwrite,
        )
    except FileNotFoundError as exc:
        print(_colored(f"Error: {exc}", "31"), file=sys.stderr)
        sys.exit(1)

    for entry in result.entries:
        if entry.status == PromoteStatus.ADDED:
            label = _colored("added", "32")
        elif entry.status == PromoteStatus.UPDATED:
            label = _colored("updated", "33")
        else:
            label = _colored("skipped", "90")
        print(f"  [{label}] {entry.key}")

    print()
    print(result.summary())

    has_changes = result.added() or result.updated()
    sys.exit(0 if has_changes or result.skipped() else 0)


def register_commands(subparsers) -> None:
    parser = subparsers.add_parser(
        "promote",
        help="Promote env vars from one file to another",
    )
    parser.add_argument("source", help="Source .env file")
    parser.add_argument("target", help="Target .env file")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to promote (default: all)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in target",
    )
    parser.set_defaults(func=cmd_promote)
