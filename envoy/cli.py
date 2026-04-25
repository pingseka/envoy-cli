"""Main CLI entry-point for envoy."""

from __future__ import annotations

import argparse
import sys

from envoy.diff import diff_env_files
from envoy import cli_sync, cli_snapshot, cli_template, cli_lint


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_diff(args: argparse.Namespace) -> None:
    result = diff_env_files(args.base, args.target)
    if not result.entries:
        print("No differences found.")
        return
    for entry in result.entries:
        line = str(entry)
        if entry.status.value == "added":
            print(_colored(line, "32"))
        elif entry.status.value == "removed":
            print(_colored(line, "31"))
        elif entry.status.value == "changed":
            print(_colored(line, "33"))
        else:
            print(line)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files across environments",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # diff
    diff_parser = subparsers.add_parser("diff", help="Diff two .env files")
    diff_parser.add_argument("base", help="Base .env file")
    diff_parser.add_argument("target", help="Target .env file")
    diff_parser.set_defaults(func=cmd_diff)

    # sync / profile
    cli_sync.register_commands(subparsers)

    # snapshot
    cli_snapshot.register_commands(subparsers)

    # template
    cli_template.register_commands(subparsers)

    # lint
    cli_lint.register_commands(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
