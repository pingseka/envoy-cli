"""CLI commands for sync and profile management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.sync import sync_env_files, write_synced_env
from envoy.profiles import Profile, ProfileStore, PROFILES_FILE


def _get_store() -> ProfileStore:
    return ProfileStore.load(Path(PROFILES_FILE))


def cmd_sync(args: argparse.Namespace) -> int:
    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"error: source file not found: {source}", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"error: target file not found: {target}", file=sys.stderr)
        return 1

    result = sync_env_files(
        source,
        target,
        overwrite=args.overwrite,
        add_missing=not args.no_add,
    )

    print(result.summary())

    if result.has_conflicts and not args.force:
        print("\nAborted. Use --force to apply changes despite conflicts.")
        return 1

    if args.write:
        write_synced_env(result)
        print(f"\nWritten to {target}")

    return 0


def cmd_profile_add(args: argparse.Namespace) -> int:
    store = _get_store()
    tags = args.tags.split(",") if args.tags else []
    profile = Profile(
        name=args.name,
        env_path=args.env_path,
        description=args.description or "",
        tags=tags,
    )
    store.add(profile)
    store.save()
    print(f"Profile '{args.name}' saved.")
    return 0


def cmd_profile_list(args: argparse.Namespace) -> int:
    store = _get_store()
    profiles = store.list_profiles()
    if not profiles:
        print("No profiles defined.")
        return 0
    for p in profiles:
        tags_str = f"  [{', '.join(p.tags)}]" if p.tags else ""
        print(f"  {p.name}: {p.env_path}{tags_str}")
        if p.description:
            print(f"    {p.description}")
    return 0


def cmd_profile_remove(args: argparse.Namespace) -> int:
    store = _get_store()
    if store.remove(args.name):
        store.save()
        print(f"Profile '{args.name}' removed.")
        return 0
    print(f"Profile '{args.name}' not found.", file=sys.stderr)
    return 1


def register_sync_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    sync_p = subparsers.add_parser("sync", help="Sync source .env into target .env")
    sync_p.add_argument("source", help="Source .env file")
    sync_p.add_argument("target", help="Target .env file")
    sync_p.add_argument("--overwrite", action="store_true", help="Overwrite differing values")
    sync_p.add_argument("--no-add", action="store_true", help="Do not add missing keys")
    sync_p.add_argument("--write", action="store_true", help="Write merged result to target")
    sync_p.add_argument("--force", action="store_true", help="Apply even if conflicts exist")
    sync_p.set_defaults(func=cmd_sync)

    profile_p = subparsers.add_parser("profile", help="Manage named env profiles")
    profile_sub = profile_p.add_subparsers(dest="profile_cmd")

    add_p = profile_sub.add_parser("add", help="Add a profile")
    add_p.add_argument("name")
    add_p.add_argument("env_path")
    add_p.add_argument("--description", default="")
    add_p.add_argument("--tags", default="")
    add_p.set_defaults(func=cmd_profile_add)

    list_p = profile_sub.add_parser("list", help="List profiles")
    list_p.set_defaults(func=cmd_profile_list)

    rm_p = profile_sub.add_parser("remove", help="Remove a profile")
    rm_p.add_argument("name")
    rm_p.set_defaults(func=cmd_profile_remove)
