"""CLI commands for snapshot management."""

from __future__ import annotations

import sys
from pathlib import Path

from envoy.snapshot import SnapshotStore, capture_snapshot, restore_snapshot

_DEFAULT_STORE = Path.home() / ".envoy" / "snapshots.json"


def _get_store(path: str | None = None) -> SnapshotStore:
    store_path = Path(path) if path else _DEFAULT_STORE
    store = SnapshotStore(store_path=store_path)
    store.load()
    return store


def cmd_snapshot_capture(args) -> None:
    store = _get_store(getattr(args, "store", None))
    env_path = args.env_file
    label = args.label
    snap = capture_snapshot(env_path, label, store)
    print(f"Snapshot captured: {snap}")


def cmd_snapshot_restore(args) -> None:
    store = _get_store(getattr(args, "store", None))
    label = args.label
    snap = store.get(label)
    if snap is None:
        print(f"Error: no snapshot found with label '{label}'", file=sys.stderr)
        sys.exit(1)
    target = getattr(args, "output", None)
    out = restore_snapshot(snap, target_path=target)
    print(f"Restored snapshot '{label}' to {out}")


def cmd_snapshot_list(args) -> None:
    store = _get_store(getattr(args, "store", None))
    snapshots = store.list_all()
    if not snapshots:
        print("No snapshots found.")
        return
    for snap in snapshots:
        print(str(snap))


def cmd_snapshot_remove(args) -> None:
    store = _get_store(getattr(args, "store", None))
    label = args.label
    removed = store.remove(label)
    if removed:
        print(f"Snapshot '{label}' removed.")
    else:
        print(f"No snapshot with label '{label}' found.", file=sys.stderr)
        sys.exit(1)


def register_snapshot_commands(subparsers) -> None:
    snap_parser = subparsers.add_parser("snapshot", help="Manage .env snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd")

    cap = snap_sub.add_parser("capture", help="Capture a snapshot of an .env file")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("label", help="Label for the snapshot")
    cap.add_argument("--store", default=None, help="Custom snapshot store path")
    cap.set_defaults(func=cmd_snapshot_capture)

    res = snap_sub.add_parser("restore", help="Restore a snapshot by label")
    res.add_argument("label", help="Label of the snapshot to restore")
    res.add_argument("--output", default=None, help="Override output path")
    res.add_argument("--store", default=None, help="Custom snapshot store path")
    res.set_defaults(func=cmd_snapshot_restore)

    ls = snap_sub.add_parser("list", help="List all snapshots")
    ls.add_argument("--store", default=None, help="Custom snapshot store path")
    ls.set_defaults(func=cmd_snapshot_list)

    rm = snap_sub.add_parser("remove", help="Remove a snapshot by label")
    rm.add_argument("label", help="Label of the snapshot to remove")
    rm.add_argument("--store", default=None, help="Custom snapshot store path")
    rm.set_defaults(func=cmd_snapshot_remove)
