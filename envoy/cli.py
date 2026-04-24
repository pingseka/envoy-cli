"""CLI entry point for envoy-cli."""

import argparse
import sys

from envoy.diff import diff_env_files, DiffStatus


STATUS_COLORS = {
    DiffStatus.ADDED: "\033[32m",     # green
    DiffStatus.REMOVED: "\033[31m",   # red
    DiffStatus.CHANGED: "\033[33m",   # yellow
    DiffStatus.UNCHANGED: "\033[0m",  # reset
}
RESET = "\033[0m"


def _colored(text: str, status: DiffStatus, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{STATUS_COLORS.get(status, '')}{text}{RESET}"


def cmd_diff(args: argparse.Namespace) -> int:
    """Handle the `envoy diff` subcommand."""
    try:
        result = diff_env_files(args.base, args.target, show_unchanged=args.all)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    use_color = not args.no_color and sys.stdout.isatty()

    if not result.has_changes and not args.all:
        print("No differences found.")
        return 0

    for entry in result.entries:
        line = _colored(str(entry), entry.status, use_color)
        print(line)

    summary = result.summary
    print(
        f"\nSummary: +{summary['added']} added, "
        f"-{summary['removed']} removed, "
        f"~{summary['changed']} changed"
    )
    return 1 if result.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser("diff", help="Diff two .env files")
    diff_parser.add_argument("base", help="Base .env file")
    diff_parser.add_argument("target", help="Target .env file to compare against")
    diff_parser.add_argument(
        "--all", "-a", action="store_true", help="Show unchanged keys too"
    )
    diff_parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "diff": cmd_diff,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":
    main()
