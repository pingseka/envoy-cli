"""CLI commands for copying keys between .env files."""

from __future__ import annotations

import sys

from envoy.copy import CopyStatus, copy_keys


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_copy(args) -> None:  # type: ignore[type-arg]
    """Handle the `envoy copy` sub-command."""
    if not args.keys:
        print("error: at least one KEY must be specified", file=sys.stderr)
        sys.exit(1)

    result = copy_keys(
        source_path=args.source,
        target_path=args.target,
        keys=args.keys,
        overwrite=args.overwrite,
    )

    for entry in result.entries:
        if entry.status == CopyStatus.COPIED:
            label = _colored("copied", "32")
        elif entry.status == CopyStatus.SKIPPED:
            label = _colored("skipped", "33")
        else:
            label = _colored("missing", "31")
        print(f"  [{label}] {entry.key}")

    print()
    print(result.summary())

    if result.not_found:
        sys.exit(2)


def register_commands(subparsers) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "copy",
        help="Copy specific keys from one .env file to another",
    )
    parser.add_argument("source", help="Source .env file path")
    parser.add_argument("target", help="Target .env file path")
    parser.add_argument("keys", nargs="+", metavar="KEY", help="Key(s) to copy")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in target (default: skip)",
    )
    parser.set_defaults(func=cmd_copy)
