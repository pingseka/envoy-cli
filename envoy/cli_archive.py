"""CLI commands for the archive feature."""
from __future__ import annotations

import os
import sys

from envoy.archive import ArchiveStatus, create_archive, extract_archive
from envoy.parser import parse_env_file


def _colored(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def cmd_archive_create(args) -> int:
    """Pack an env file into a zip archive."""
    if not os.path.isfile(args.env_file):
        print(_colored(f"error: file not found: {args.env_file}", "31"), file=sys.stderr)
        return 1

    env_data = parse_env_file(args.env_file)
    entry = create_archive(
        env_path=args.env_file,
        archive_path=args.output,
        env_data=env_data,
        label=getattr(args, "label", None),
    )

    if entry.status == ArchiveStatus.CREATED:
        print(_colored(str(entry), "32"))
        return 0
    print(_colored(f"error: {entry.message}", "31"), file=sys.stderr)
    return 1


def cmd_archive_extract(args) -> int:
    """Unpack a zip archive into a directory."""
    dest = getattr(args, "dest", ".")
    os.makedirs(dest, exist_ok=True)

    entry = extract_archive(archive_path=args.archive, dest_dir=dest)

    if entry.status == ArchiveStatus.EXTRACTED:
        print(_colored(str(entry), "32"))
        return 0
    print(_colored(f"error: {entry.message}", "31"), file=sys.stderr)
    return 1


def register_commands(subparsers) -> None:
    # archive create
    p_create = subparsers.add_parser("archive-create", help="Pack an env file into a zip archive")
    p_create.add_argument("env_file", help="Source .env file")
    p_create.add_argument("output", help="Destination archive path (.zip)")
    p_create.add_argument("--label", default="", help="Optional label stored in metadata")
    p_create.set_defaults(func=cmd_archive_create)

    # archive extract
    p_extract = subparsers.add_parser("archive-extract", help="Unpack an env archive")
    p_extract.add_argument("archive", help="Archive file to extract (.zip)")
    p_extract.add_argument("--dest", default=".", help="Destination directory (default: .)")
    p_extract.set_defaults(func=cmd_archive_extract)
