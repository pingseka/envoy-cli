"""CLI command for reordering keys in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.parser import serialize_env
from envoy.reorder import ReorderStatus, reorder_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_reorder(args: argparse.Namespace) -> int:
    source = Path(args.file)
    if not source.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1

    order: list[str] = args.keys or []

    if not order:
        print("Error: no key order specified (use --keys or --alpha)", file=sys.stderr)
        return 1

    if args.alpha:
        from envoy.parser import parse_env_file
        env = parse_env_file(source)
        order = sorted(env.keys())

    result = reorder_env(source, order, append_unspecified=not args.drop)

    for entry in result.entries:
        if entry.status == ReorderStatus.MOVED:
            label = _colored("MOVED", "33")
        elif entry.status == ReorderStatus.UNSPECIFIED:
            label = _colored("APPENDED", "36")
        else:
            label = _colored("OK", "32")
        if args.verbose:
            print(f"  [{label}] {entry}")

    if args.write:
        dest = Path(args.output) if args.output else source
        dest.write_text(serialize_env(result.env))
        print(_colored(f"Written to {dest}", "32"))
    else:
        print(serialize_env(result.env))

    print(_colored(result.summary(), "90"), file=sys.stderr)
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("reorder", help="Reorder keys in a .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Desired key order")
    p.add_argument("--alpha", action="store_true", help="Sort keys alphabetically")
    p.add_argument("--drop", action="store_true", help="Drop keys not listed in --keys")
    p.add_argument("--write", action="store_true", help="Write result back to file")
    p.add_argument("--output", metavar="FILE", help="Write to a different output file")
    p.add_argument("--verbose", "-v", action="store_true", help="Show per-key status")
    p.set_defaults(func=cmd_reorder)
