"""CLI commands for the transform feature."""
from __future__ import annotations

import argparse
import sys

from envoy.parser import serialize_env
from envoy.transform import transform_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_transform(args: argparse.Namespace) -> int:
    """Apply a built-in transformation to values in an env file."""
    op = args.operation

    if op == "upper":
        fn = lambda k, v: v.upper() if v != v.upper() else None  # noqa: E731
    elif op == "lower":
        fn = lambda k, v: v.lower() if v != v.lower() else None  # noqa: E731
    elif op == "strip":
        fn = lambda k, v: v.strip() if v != v.strip() else None  # noqa: E731
    elif op == "prefix":
        prefix = args.value or ""
        fn = lambda k, v: f"{prefix}{v}"  # noqa: E731
    elif op == "suffix":
        suffix = args.value or ""
        fn = lambda k, v: f"{v}{suffix}"  # noqa: E731
    else:
        print(f"Unknown operation: {op}", file=sys.stderr)
        return 2

    keys = args.keys.split(",") if args.keys else None

    result = transform_env(args.file, fn, keys=keys)

    if not result.changed():
        print(_colored("No values changed.", "33"))
        return 0

    for entry in result.changed():
        print(_colored(f"  ~ {entry}", "36"))

    if args.write:
        serialized = serialize_env(result.env)
        with open(args.file, "w") as fh:
            fh.write(serialized)
        print(_colored(f"Written to {args.file}", "32"))

    print(result.summary())
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("transform", help="Transform values in an env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "operation",
        choices=["upper", "lower", "strip", "prefix", "suffix"],
        help="Transformation to apply",
    )
    p.add_argument("--keys", default=None, help="Comma-separated list of keys to target")
    p.add_argument("--value", default=None, help="Argument for prefix/suffix operations")
    p.add_argument("--write", action="store_true", help="Write result back to file")
    p.set_defaults(func=cmd_transform)
