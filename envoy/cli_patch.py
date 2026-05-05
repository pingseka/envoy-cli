"""CLI commands for patching env files."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional

from envoy.parser import serialize_env
from envoy.patch import patch_env


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_patch(args: argparse.Namespace) -> int:
    """Apply key=value or key= (delete) patches to an env file."""
    patches: Dict[str, Optional[str]] = {}

    for raw in args.patches:
        if "=" not in raw:
            print(
                _colored(f"error: invalid patch '{raw}' — use KEY=VALUE or KEY= to delete", "31"),
                file=sys.stderr,
            )
            return 2
        key, _, value = raw.partition("=")
        key = key.strip()
        if not key:
            print(_colored(f"error: empty key in patch '{raw}'", "31"), file=sys.stderr)
            return 2
        patches[key] = value if value != "" else None

    try:
        result = patch_env(args.file, patches)
    except FileNotFoundError:
        print(_colored(f"error: file not found: {args.file}", "31"), file=sys.stderr)
        return 1

    for entry in result.entries:
        print(_colored(str(entry), "33"))

    if args.write:
        content = serialize_env(result.env)
        with open(args.file, "w") as fh:
            fh.write(content)
        print(_colored(f"✔ written to {args.file} ({result.summary()})", "32"))
    else:
        print()
        print(serialize_env(result.env))

    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("patch", help="Apply key-value patches to an env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "patches",
        nargs="+",
        metavar="KEY=VALUE",
        help="Patches to apply. Use KEY= (empty value) to delete a key.",
    )
    p.add_argument(
        "--write",
        "-w",
        action="store_true",
        help="Write changes back to the file in-place",
    )
    p.set_defaults(func=cmd_patch)
