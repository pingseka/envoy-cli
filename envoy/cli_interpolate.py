"""CLI command for variable interpolation in .env files."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.parser import parse_env_file, serialize_env
from envoy.interpolate import interpolate_env, InterpolateStatus


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_interpolate(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    context: Optional[dict] = None
    if args.context:
        try:
            context = parse_env_file(args.context)
        except FileNotFoundError:
            print(f"error: context file not found: {args.context}", file=sys.stderr)
            return 1

    result = interpolate_env(env, context)

    if args.check:
        unresolved = result.unresolved()
        if unresolved:
            for e in unresolved:
                print(
                    _colored("UNRESOLVED", "31")
                    + f"  {e.key}: missing {e.missing}"
                )
            return 1
        print(_colored("ok", "32") + "  all references resolved")
        return 0

    if args.inplace:
        serialized = serialize_env(result.to_dict())
        with open(args.file, "w") as fh:
            fh.write(serialized)
        print(f"wrote interpolated env to {args.file}")
        return 0

    for entry in result.entries:
        if entry.status == InterpolateStatus.RESOLVED:
            label = _colored("resolved", "32")
        elif entry.status == InterpolateStatus.UNRESOLVED:
            label = _colored("unresolved", "31")
        else:
            label = _colored("unchanged", "90")
        print(f"{label}  {entry}")

    unresolved = result.unresolved()
    print()
    print(result.summary())
    return 1 if unresolved else 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "interpolate",
        help="resolve $VAR / ${VAR} references in an .env file",
    )
    p.add_argument("file", help=".env file to interpolate")
    p.add_argument(
        "--context",
        metavar="FILE",
        help="additional .env file supplying extra variable values",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if any references are unresolved (no output written)",
    )
    p.add_argument(
        "--inplace",
        action="store_true",
        help="write resolved values back to the file",
    )
    p.set_defaults(func=cmd_interpolate)
