"""CLI command for splitting .env files by prefix."""

from __future__ import annotations

import sys

from envoy.split import split_env_by_prefix, SplitStatus


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_split(args) -> int:
    if not args.prefixes:
        print("error: at least one --prefix is required", file=sys.stderr)
        return 2

    try:
        result = split_env_by_prefix(
            source=args.file,
            output_dir=args.output_dir,
            prefixes=args.prefixes,
            strip_prefix=args.strip_prefix,
            dry_run=args.dry_run,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for entry in result.entries:
        if entry.status == SplitStatus.WRITTEN:
            label = _colored("written", "32")
            keys_str = ", ".join(entry.keys) if entry.keys else "(none)"
            print(f"  {label}  {entry.output_file}  [{keys_str}]")
        else:
            label = _colored("skipped", "33")
            print(f"  {label}  {entry.output_file}  (no matching keys)")

    if result.unmatched:
        print(_colored(f"\nUnmatched keys: {', '.join(result.unmatched)}", "33"))

    print(f"\n{result.summary()}")

    if args.dry_run:
        print(_colored("(dry-run: no files written)", "36"))

    return 0


def register_commands(subparsers) -> None:
    p = subparsers.add_parser("split", help="Split .env file into multiple files by prefix")
    p.add_argument("file", help="Source .env file")
    p.add_argument("output_dir", help="Directory to write split files into")
    p.add_argument(
        "--prefix",
        dest="prefixes",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Prefix to split on (repeatable)",
    )
    p.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove prefix from keys in output files",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be written without writing files",
    )
    p.set_defaults(func=cmd_split)
