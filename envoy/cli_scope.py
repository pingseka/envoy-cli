"""CLI commands for scope filtering."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.parser import parse_env_file, serialize_env
from envoy.scope import filter_by_keys, filter_by_pattern, filter_by_prefix


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_scope(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.prefix:
        result = filter_by_prefix(
            env,
            args.prefix,
            scope_name=args.name,
            strip_prefix=args.strip_prefix,
        )
    elif args.pattern:
        result = filter_by_pattern(env, args.pattern, scope_name=args.name)
    elif args.keys:
        result = filter_by_keys(env, args.keys, scope_name=args.name)
    else:
        print("Error: one of --prefix, --pattern, or --keys is required.", file=sys.stderr)
        return 1

    if args.output:
        try:
            with open(args.output, "w") as fh:
                fh.write(serialize_env(result.matched))
            print(_colored(f"Written {len(result.matched)} keys to {args.output}", "32"))
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 1
    else:
        print(serialize_env(result.matched), end="")

    if not args.quiet:
        print(_colored(result.summary(), "36"), file=sys.stderr)

    return 0


def register_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("scope", help="Filter env keys by prefix, pattern, or explicit list")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--prefix", help="Keep keys starting with PREFIX")
    p.add_argument("--strip-prefix", action="store_true", help="Remove prefix from matched keys")
    p.add_argument("--pattern", help="Keep keys matching regex PATTERN")
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Explicit list of keys to keep")
    p.add_argument("--name", help="Human-readable scope name for summary")
    p.add_argument("-o", "--output", help="Write result to file instead of stdout")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress summary line")
    p.set_defaults(func=cmd_scope)
