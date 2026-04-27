"""CLI commands for the mask feature."""

from __future__ import annotations

import argparse
import sys

from envoy.mask import mask_env
from envoy.parser import serialize_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_mask(args: argparse.Namespace) -> int:
    """Mask keys in an env file and print the result."""
    keys = args.keys or []
    pattern = getattr(args, "pattern", None)
    auto_secrets = getattr(args, "auto_secrets", False)

    if not keys and not pattern and not auto_secrets:
        print(_colored("error: specify --keys, --pattern, or --auto-secrets", "31"), file=sys.stderr)
        return 1

    try:
        result = mask_env(
            env_path=args.file,
            keys=keys,
            pattern=pattern,
            auto_secrets=auto_secrets,
        )
    except FileNotFoundError:
        print(_colored(f"error: file not found: {args.file}", "31"), file=sys.stderr)
        return 1

    if args.output:
        serialized = serialize_env(result.masked_env)
        with open(args.output, "w") as fh:
            fh.write(serialized)
        print(_colored(f"Written to {args.output}", "32"))
    else:
        for key, value in result.masked_env.items():
            print(f"{key}={value}")

    if args.verbose:
        print()
        for entry in result.entries:
            print(str(entry))
        print(_colored(result.summary(), "36"))

    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("mask", help="Mask secret values in an env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Keys to mask")
    p.add_argument("--pattern", metavar="REGEX", help="Mask keys matching regex pattern")
    p.add_argument(
        "--auto-secrets",
        action="store_true",
        default=False,
        help="Automatically mask keys that look like secrets",
    )
    p.add_argument("--output", "-o", metavar="FILE", help="Write masked env to file")
    p.add_argument("--verbose", "-v", action="store_true", default=False)
    p.set_defaults(func=cmd_mask)
