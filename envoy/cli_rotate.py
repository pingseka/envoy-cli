"""CLI commands for bulk key rotation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from envoy.rotate import RotateStatus, apply_rotation, rotate_keys


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def cmd_rotate(args) -> int:  # noqa: ANN001
    """Rotate (bulk-rename) keys in a .env file.

    Mapping is supplied as KEY=NEW_KEY pairs via --map.
    """
    env_path = Path(args.file)
    if not env_path.exists():
        print(_colored(f"error: file not found: {env_path}", "31"), file=sys.stderr)
        return 1

    if not args.map:
        print(_colored("error: at least one --map OLD=NEW pair is required", "31"), file=sys.stderr)
        return 1

    mapping: dict[str, str] = {}
    for pair in args.map:
        if "=" not in pair:
            print(_colored(f"error: invalid mapping '{pair}' (expected OLD=NEW)", "31"), file=sys.stderr)
            return 1
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()

    result = rotate_keys(env_path, mapping)

    for entry in result.entries:
        if entry.status == RotateStatus.RENAMED:
            print(_colored(f"  renamed: {entry.old_key} -> {entry.new_key}", "32"))
        elif entry.status == RotateStatus.NOT_FOUND:
            print(_colored(f"  not found: {entry.old_key}", "33"))
        elif entry.status == RotateStatus.CONFLICT:
            print(_colored(f"  conflict: {entry.new_key} already exists (skipped {entry.old_key})", "31"))

    if result.conflicts() or result.not_found():
        print(_colored(f"\nrotation incomplete: {result.summary()}", "33"))
        return 1

    if not args.dry_run:
        apply_rotation(env_path, result)
        print(_colored(f"\n{result.summary()} — written to {env_path}", "32"))
    else:
        print(_colored(f"\ndry-run: {result.summary()} (no changes written)", "36"))

    return 0


def register_commands(subparsers) -> None:  # noqa: ANN001
    p = subparsers.add_parser("rotate", help="Bulk-rename keys in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--map",
        metavar="OLD=NEW",
        action="append",
        help="Key mapping (repeatable): OLD_KEY=NEW_KEY",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk",
    )
    p.set_defaults(func=cmd_rotate)
