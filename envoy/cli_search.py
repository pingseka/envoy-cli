"""CLI command for searching env files."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.parser import parse_env_file
from envoy.search import search_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_search(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    key_pattern: Optional[str] = getattr(args, "key", None) or None
    value_pattern: Optional[str] = getattr(args, "value", None) or None

    if not key_pattern and not value_pattern:
        print("Error: provide --key and/or --value pattern", file=sys.stderr)
        return 1

    try:
        result = search_env(
            env,
            key_pattern=key_pattern,
            value_pattern=value_pattern,
            case_sensitive=args.case_sensitive,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not result.matches:
        print(_colored("No matches found.", "33"))
        return 1

    for match in result.matches:
        key_str = _colored(match.key, "36")
        val_str = _colored(match.display_value(), "33" if match.is_secret else "32")
        print(f"  {key_str}={val_str}")

    print()
    print(_colored(result.summary(), "90"))
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("search", help="Search keys/values in an env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--key", default="", help="Regex pattern to match against keys")
    p.add_argument("--value", default="", help="Regex pattern to match against values")
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive matching",
    )
    p.set_defaults(func=cmd_search)
