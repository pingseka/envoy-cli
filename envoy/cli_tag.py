"""CLI commands for tagging .env keys."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.tag import TagStatus, keys_for_tag, tag_keys


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_tag(args: argparse.Namespace) -> None:
    """Apply one or more tags to specified keys in an env file."""
    raw: List[str] = args.key_tag  # list of "KEY:tag" strings
    mapping: dict[str, list[str]] = {}
    for item in raw:
        if ":" not in item:
            print(_colored(f"Invalid format '{item}' — expected KEY:tag", "31"), file=sys.stderr)
            sys.exit(2)
        key, tag = item.split(":", 1)
        mapping.setdefault(key.strip(), []).append(tag.strip())

    meta_path: str = args.meta or (args.env_file + ".tags.json")
    result = tag_keys(args.env_file, mapping, meta_path=meta_path)

    for entry in result.entries:
        if entry.status == TagStatus.TAGGED:
            print(_colored(str(entry), "32"))
        elif entry.status == TagStatus.ALREADY_TAGGED:
            print(_colored(str(entry), "33"))
        else:
            print(_colored(str(entry), "31"), file=sys.stderr)

    print(result.summary())
    if result.not_found():
        sys.exit(1)


def cmd_tag_list(args: argparse.Namespace) -> None:
    """List all keys that carry a given tag."""
    import os

    meta_path: str = args.meta or (args.env_file + ".tags.json")
    if not os.path.exists(meta_path):
        print(_colored("No tag metadata found.", "33"))
        sys.exit(0)

    keys = keys_for_tag(meta_path, args.tag)
    if not keys:
        print(f"No keys tagged with '{args.tag}'.")
    else:
        for k in keys:
            print(k)


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # tag apply
    p_tag = subparsers.add_parser("tag", help="Tag keys in a .env file")
    p_tag.add_argument("env_file", help="Path to the .env file")
    p_tag.add_argument(
        "key_tag",
        nargs="+",
        metavar="KEY:tag",
        help="Key/tag pairs, e.g. DB_PASSWORD:secret",
    )
    p_tag.add_argument("--meta", default=None, help="Path to tag sidecar JSON (default: <env_file>.tags.json)")
    p_tag.set_defaults(func=cmd_tag)

    # tag list
    p_list = subparsers.add_parser("tag-list", help="List keys with a given tag")
    p_list.add_argument("env_file", help="Path to the .env file (used to derive default meta path)")
    p_list.add_argument("tag", help="Tag label to look up")
    p_list.add_argument("--meta", default=None, help="Path to tag sidecar JSON")
    p_list.set_defaults(func=cmd_tag_list)
