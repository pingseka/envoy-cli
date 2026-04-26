"""CLI commands for renaming .env keys."""

import argparse
import sys
from envoy.rename import rename_keys


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_rename(args: argparse.Namespace) -> int:
    """Rename one or more keys in a .env file."""
    if len(args.rename) % 2 != 0:
        print(
            _colored("error: rename pairs must be given as OLD NEW OLD NEW ...", "31"),
            file=sys.stderr,
        )
        return 2

    renames = {}
    it = iter(args.rename)
    for old, new in zip(it, it):
        renames[old] = new

    result = rename_keys(
        env_file=args.file,
        renames=renames,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )

    for entry in result.entries:
        if entry.skipped:
            print(_colored(str(entry), "33"))
        else:
            label = "(dry-run) " if args.dry_run else ""
            print(_colored(f"{label}{entry}", "32"))

    print(result.summary())

    if args.dry_run and result.has_renames():
        print(_colored("dry-run: no changes written.", "36"))

    return 0 if result.skipped == 0 else 1


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("rename", help="Rename keys in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "rename",
        nargs="+",
        metavar="OLD NEW",
        help="Pairs of OLD_KEY NEW_KEY to rename",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow rename even if the new key already exists",
    )
    p.set_defaults(func=cmd_rename)
