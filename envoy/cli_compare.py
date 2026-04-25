"""CLI commands for comparing .env files."""
from __future__ import annotations

import argparse
import sys

from envoy.compare import compare_env_files, ChangeType


_COLORS = {
    ChangeType.ADDED: "\033[32m",
    ChangeType.REMOVED: "\033[31m",
    ChangeType.MODIFIED: "\033[33m",
    ChangeType.UNCHANGED: "\033[37m",
}
_RESET = "\033[0m"


def _colored(text: str, change: ChangeType, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{_COLORS.get(change, '')}{text}{_RESET}"


def cmd_compare(args: argparse.Namespace) -> int:
    """Run the compare command and print results."""
    use_color = not getattr(args, "no_color", False)
    include_unchanged = getattr(args, "all", False)

    try:
        result = compare_env_files(args.base, args.target,
                                   include_unchanged=include_unchanged)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not result.has_changes and not include_unchanged:
        print("No differences found.")
        return 0

    for entry in result.entries:
        line = str(entry)
        print(_colored(line, entry.change, use_color))

    print()
    print(result.summary())
    return 0 if not result.has_changes else 1


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the compare subcommand."""
    p = subparsers.add_parser(
        "compare",
        help="Compare two .env files and show differences",
    )
    p.add_argument("base", help="Base .env file path")
    p.add_argument("target", help="Target .env file path")
    p.add_argument("--all", action="store_true",
                   help="Include unchanged keys in output")
    p.add_argument("--no-color", action="store_true",
                   help="Disable colored output")
    p.set_defaults(func=cmd_compare)
