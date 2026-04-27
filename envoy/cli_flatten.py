"""CLI commands for the flatten feature."""
from __future__ import annotations

import argparse
import sys

from envoy.flatten import flatten_env
from envoy.parser import serialize_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_flatten(args: argparse.Namespace) -> int:
    """Flatten an env file, optionally stripping a key prefix."""
    try:
        result = flatten_env(
            path=args.file,
            strip_prefix=args.strip_prefix or "",
            keep_first=not args.keep_last,
        )
    except FileNotFoundError:
        print(_colored(f"error: file not found: {args.file}", "31"), file=sys.stderr)
        return 1

    if args.dry_run:
        for entry in result.entries:
            print(str(entry))
        print(_colored(result.summary(), "36"))
        return 0

    flattened = result.to_dict()

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(serialize_env(flattened))
        print(_colored(f"Written to {args.output}", "32"))
    else:
        print(serialize_env(flattened), end="")

    if args.verbose:
        print(_colored(result.summary(), "36"), file=sys.stderr)

    dups = result.duplicates()
    if dups:
        return 2  # non-zero but not fatal — caller can decide
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("flatten", help="Flatten and deduplicate an env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("--strip-prefix", default="", metavar="PREFIX",
                   help="Remove this prefix from all matching keys")
    p.add_argument("--keep-last", action="store_true",
                   help="When duplicates exist, keep the last value (default: keep first)")
    p.add_argument("--output", "-o", default="", metavar="FILE",
                   help="Write result to FILE instead of stdout")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would change without writing")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print summary to stderr")
    p.set_defaults(func=cmd_flatten)
