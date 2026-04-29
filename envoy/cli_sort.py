"""CLI commands for sorting .env file keys."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envoy.sort import SortOrder, sort_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_sort(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(_colored(f"Error: file not found: {path}", "31"), file=sys.stderr)
        return 1

    try:
        order = SortOrder(args.order)
    except ValueError:
        print(
            _colored(f"Error: invalid order '{args.order}'. Use 'asc' or 'desc'.", "31"),
            file=sys.stderr,
        )
        return 1

    result = sort_env(
        path,
        order=order,
        write=not args.dry_run,
        group_prefixes=args.group_prefixes,
    )

    if args.dry_run:
        print(_colored("[dry-run] Proposed sorted order:", "33"))
        for key in result.sorted_order:
            print(f"  {key}={result.env[key]}")
        print()

    if result.changed:
        print(_colored(result.summary(), "32"))
    else:
        print(result.summary())

    if not args.dry_run and result.changed:
        print(_colored(f"Written to {path}", "36"))

    return 0


def register_commands(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "sort",
        help="Sort keys in a .env file alphabetically.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--order",
        default="asc",
        choices=["asc", "desc"],
        help="Sort order: 'asc' (default) or 'desc'.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sorted output without writing.",
    )
    p.add_argument(
        "--group-prefixes",
        action="store_true",
        help="Group keys by their prefix before sorting.",
    )
    p.set_defaults(func=cmd_sort)
