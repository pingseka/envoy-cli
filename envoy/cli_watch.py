"""CLI sub-commands for the watch feature."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import List

from envoy.watch import EnvWatcher, WatchEvent


def _colored(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _make_handler(verbose: bool) -> "Callable[[WatchEvent], None]":
    from typing import Callable

    def handler(event: WatchEvent) -> None:
        label = _colored("CHANGED", "33")
        print(f"[{label}] {event.path}")
        if verbose and event.changed_keys:
            for key in event.changed_keys:
                print(f"  {_colored('~', '36')} {key}")

    return handler


def cmd_watch(args: Namespace) -> None:
    """Watch one or more .env files for changes."""
    paths: List[str] = args.files
    interval: float = args.interval
    verbose: bool = getattr(args, "verbose", False)

    if not paths:
        print(_colored("error:", "31") + " no files specified", file=sys.stderr)
        sys.exit(1)

    watcher = EnvWatcher(paths, interval=interval)
    watcher.on_change(_make_handler(verbose))

    print(
        _colored("Watching", "32")
        + f" {len(paths)} file(s) — press Ctrl+C to stop"
    )
    for p in paths:
        print(f"  {_colored('+', '32')} {p}")

    watcher.watch()


def register_commands(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "watch",
        help="Watch .env file(s) for changes and print diffs",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to watch")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="polling interval in seconds (default: 1.0)",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="show individual changed keys",
    )
    p.set_defaults(func=cmd_watch)
