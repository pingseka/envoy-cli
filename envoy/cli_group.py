"""CLI commands for grouping env keys."""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from envoy.parser import parse_env_file
from envoy.group import group_by_prefix, group_by_pattern


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_group(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.pattern:
        raw_patterns: Dict[str, str] = {}
        for item in args.pattern:
            if "=" not in item:
                print(f"error: pattern must be name=regex, got: {item}", file=sys.stderr)
                return 1
            name, _, pat = item.partition("=")
            raw_patterns[name.strip()] = pat.strip()
        result = group_by_pattern(env, raw_patterns)
    else:
        prefixes = args.prefix or []
        result = group_by_prefix(env, prefixes, strip_prefix=args.strip_prefix)

    for group_name, keys in result.groups.items():
        header = _colored(f"[{group_name}]", "1;34")
        print(header)
        if keys:
            for k, v in keys.items():
                print(f"  {k}={v}")
        else:
            print("  (empty)")

    if result.ungrouped:
        print(_colored("[ungrouped]", "1;33"))
        for k, v in result.ungrouped.items():
            print(f"  {k}={v}")

    print(_colored(f"\nSummary: {result.summary()}", "2"))
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("group", help="Group env keys by prefix or pattern")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--prefix", metavar="PREFIX", nargs="+", help="One or more key prefixes")
    p.add_argument(
        "--pattern",
        metavar="NAME=REGEX",
        nargs="+",
        help="Named regex patterns, e.g. db=^DB_ cache=^CACHE_",
    )
    p.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove matched prefix from output keys (prefix mode only)",
    )
    p.set_defaults(func=cmd_group)
