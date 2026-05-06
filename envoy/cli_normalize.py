"""CLI commands for normalizing .env files."""

from __future__ import annotations

import argparse
import sys

from envoy.normalize import normalize_env
from envoy.parser import serialize_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_normalize(args: argparse.Namespace) -> int:
    try:
        result = normalize_env(
            path=args.file,
            key_case=args.key_case,
            strip_values=args.strip_values,
            unquote_values=args.unquote_values,
        )
    except FileNotFoundError:
        print(_colored(f"error: file not found: {args.file}", "31"), file=sys.stderr)
        return 1

    changed = result.changed()

    if not changed:
        print(_colored("✓ Nothing to normalize.", "32"))
        return 0

    for entry in changed:
        key_part = ""
        if entry.original_key != entry.normalized_key:
            key_part = (
                _colored(entry.original_key, "33")
                + " -> "
                + _colored(entry.normalized_key, "32")
            )
        else:
            key_part = _colored(entry.normalized_key, "32")

        val_part = ""
        if entry.original_value != entry.normalized_value:
            val_part = (
                _colored(repr(entry.original_value), "33")
                + " -> "
                + _colored(repr(entry.normalized_value), "32")
            )
        ops = ", ".join(op.value for op in entry.ops_applied)
        print(f"  {key_part}: {val_part}  [{ops}]")

    print()
    print(_colored(result.summary(), "36"))

    if args.write:
        serialized = serialize_env(result.output)
        with open(args.file, "w") as fh:
            fh.write(serialized)
        print(_colored(f"✓ Written to {args.file}", "32"))

    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "normalize",
        help="Normalize keys and values in a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--key-case",
        choices=["upper", "lower"],
        default=None,
        dest="key_case",
        help="Normalize key casing",
    )
    p.add_argument(
        "--strip-values",
        action="store_true",
        default=False,
        dest="strip_values",
        help="Strip leading/trailing whitespace from values",
    )
    p.add_argument(
        "--unquote-values",
        action="store_true",
        default=False,
        dest="unquote_values",
        help="Remove surrounding quotes from values",
    )
    p.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write normalized output back to the file",
    )
    p.set_defaults(func=cmd_normalize)
