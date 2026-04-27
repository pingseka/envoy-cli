"""CLI commands for pinning env var keys to required values."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional

from envoy.pin import PinViolationKind, check_pins


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _parse_pin_arg(raw: str) -> tuple[str, Optional[str]]:
    """Parse 'KEY=value' or just 'KEY' into (key, value_or_None)."""
    if "=" in raw:
        key, _, value = raw.partition("=")
        return key.strip(), value
    return raw.strip(), None


def cmd_pin(args: argparse.Namespace) -> None:
    """Enforce pinned key/value constraints on an env file."""
    pins: Dict[str, Optional[str]] = {}
    for raw in args.pins:
        key, value = _parse_pin_arg(raw)
        pins[key] = value

    result = check_pins(args.env_file, pins)

    if result.ok:
        print(_colored("✔ All pinned keys satisfied.", "32"))
        sys.exit(0)
    else:
        for v in result.violations:
            if v.kind == PinViolationKind.MISSING:
                label = _colored("MISSING", "31")
            elif v.kind == PinViolationKind.VALUE_MISMATCH:
                label = _colored("MISMATCH", "33")
            else:
                label = _colored("PATTERN", "35")
            print(f"{label}  {v}")
        sys.exit(1)


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "pin",
        help="Enforce required keys (and optional values) in an env file",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "pins",
        nargs="+",
        metavar="KEY[=value]",
        help=(
            "Key to require. Append =value to enforce exact match, "
            "or =re:<pattern> for regex match."
        ),
    )
    p.set_defaults(func=cmd_pin)
