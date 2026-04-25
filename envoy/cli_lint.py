"""CLI commands for the lint feature."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.lint import lint_env_file, LintSeverity


def cmd_lint(args: argparse.Namespace) -> None:
    """Lint one or more .env files and report issues."""
    exit_code = 0

    for path in args.files:
        try:
            result = lint_env_file(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            exit_code = 2
            continue

        if not result.issues:
            if not args.quiet:
                print(f"{path}: OK")
            continue

        for issue in result.issues:
            color = _severity_color(issue.severity)
            reset = "\033[0m" if color else ""
            print(f"{path}:{color}{issue}{reset}")

        if result.has_errors():
            exit_code = 1

    sys.exit(exit_code)


def _severity_color(severity: LintSeverity) -> str:
    return {
        LintSeverity.ERROR: "\033[31m ",
        LintSeverity.WARNING: "\033[33m ",
    }.get(severity, "")


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "lint",
        help="Lint .env files for style and correctness issues",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to lint",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress OK messages; only print issues",
    )
    parser.set_defaults(func=cmd_lint)
