"""Main CLI entry point for envoy."""

import argparse
import sys

from envoy.cli_sync import cmd_sync, cmd_profile_add, cmd_profile_list, cmd_profile_remove
from envoy.cli_snapshot import (
    cmd_snapshot_capture,
    cmd_snapshot_restore,
    cmd_snapshot_list,
    cmd_snapshot_remove,
)
from envoy.cli_template import register_commands as register_template_commands


def _colored(text: str, color: str) -> str:
    codes = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "reset": "\033[0m"}
    return f"{codes.get(color, '')}{text}{codes['reset']}"


def cmd_diff(args: argparse.Namespace) -> int:
    from envoy.diff import diff_env_files

    result = diff_env_files(args.base, args.target)
    for entry in result.entries:
        print(entry)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # diff
    diff_parser = subparsers.add_parser("diff", help="Show diff between two .env files")
    diff_parser.add_argument("base", help="Base .env file")
    diff_parser.add_argument("target", help="Target .env file")
    diff_parser.set_defaults(func=cmd_diff)

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync variables from source to target")
    sync_parser.add_argument("source")
    sync_parser.add_argument("target")
    sync_parser.add_argument("--force", action="store_true")
    sync_parser.set_defaults(func=cmd_sync)

    # profile
    profile_parser = subparsers.add_parser("profile", help="Manage profiles")
    profile_sub = profile_parser.add_subparsers(dest="profile_command")

    add_p = profile_sub.add_parser("add")
    add_p.add_argument("name")
    add_p.add_argument("path")
    add_p.set_defaults(func=cmd_profile_add)

    list_p = profile_sub.add_parser("list")
    list_p.set_defaults(func=cmd_profile_list)

    remove_p = profile_sub.add_parser("remove")
    remove_p.add_argument("name")
    remove_p.set_defaults(func=cmd_profile_remove)

    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Manage snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_command")

    cap = snap_sub.add_parser("capture")
    cap.add_argument("file")
    cap.add_argument("--label", default=None)
    cap.set_defaults(func=cmd_snapshot_capture)

    restore = snap_sub.add_parser("restore")
    restore.add_argument("snapshot_id")
    restore.add_argument("output")
    restore.set_defaults(func=cmd_snapshot_restore)

    ls = snap_sub.add_parser("list")
    ls.set_defaults(func=cmd_snapshot_list)

    rm = snap_sub.add_parser("remove")
    rm.add_argument("snapshot_id")
    rm.set_defaults(func=cmd_snapshot_remove)

    # template / render
    register_template_commands(subparsers)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
