"""CLI commands for quoting/unquoting .env values."""

from __future__ import annotations

import sys

from envoy.parser import serialize_env
from envoy.quote import QuoteStyle, QuoteStatus, quote_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_quote(args) -> int:  # type: ignore[type-arg]
    style_map = {
        "double": QuoteStyle.DOUBLE,
        "single": QuoteStyle.SINGLE,
        "none": QuoteStyle.NONE,
    }
    style = style_map.get(args.style, QuoteStyle.DOUBLE)
    keys = args.keys if args.keys else None

    try:
        result = quote_env(args.file, style=style, keys=keys)
    except FileNotFoundError:
        print(_colored(f"error: file not found: {args.file}", "31"), file=sys.stderr)
        return 1

    for entry in result.entries:
        if entry.status == QuoteStatus.SKIPPED:
            print(_colored(f"  skip  {entry.key}", "90"))
        elif entry.status == QuoteStatus.UNQUOTED:
            print(_colored(f"  strip {entry.key}", "33"))
        else:
            print(_colored(f"  quote {entry.key}", "32"))

    if args.inplace:
        serialized = serialize_env(result.env)
        with open(args.file, "w") as fh:
            fh.write(serialized)
        print(_colored(f"\nWrote {args.file} ({result.summary()})", "36"))
    elif args.output:
        serialized = serialize_env(result.env)
        with open(args.output, "w") as fh:
            fh.write(serialized)
        print(_colored(f"\nWrote {args.output} ({result.summary()})", "36"))
    else:
        print()
        print(serialize_env(result.env))

    return 0


def register_commands(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("quote", help="Re-quote values in a .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--style",
        choices=["double", "single", "none"],
        default="double",
        help="Quoting style to apply (default: double)",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only requote these keys",
    )
    p.add_argument(
        "--inplace",
        action="store_true",
        help="Overwrite the source file",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write result to this file",
    )
    p.set_defaults(func=cmd_quote)
