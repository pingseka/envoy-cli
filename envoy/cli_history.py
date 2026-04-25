"""CLI commands for viewing .env change history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.history import HistoryLog
from envoy.parser import _is_secret_key


_RESET = "\033[0m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


def _colored(text: str, code: str, use_color: bool = True) -> str:
    return f"{code}{text}{_RESET}" if use_color else text


def _mask(key: str, value: str | None) -> str:
    if value is None:
        return "(none)"
    if _is_secret_key(key):
        return "***"
    return value


def cmd_history_show(args: argparse.Namespace) -> int:
    log_path = Path(args.log)
    log = HistoryLog(path=log_path)
    log.load()

    entries = log.for_key(args.key) if args.key else log.recent(args.last)

    if not entries:
        print("No history entries found.")
        return 0

    use_color = not args.no_color
    for entry in entries:
        ts = _colored(entry.timestamp, _DIM, use_color)
        action = _colored(entry.action.upper(), _CYAN, use_color)
        key = _colored(entry.key, _YELLOW, use_color)
        old = _mask(entry.key, entry.old_value)
        new = _mask(entry.key, entry.new_value)
        line = f"{ts}  {action}  {key}  {old} -> {new}"
        if entry.author:
            line += f"  [{entry.author}]"
        if entry.note:
            line += f"  # {entry.note}"
        print(line)

    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    log_path = Path(args.log)
    log = HistoryLog(path=log_path)
    log.load()
    count = len(log.entries)
    log.entries.clear()
    log.save()
    print(f"Cleared {count} history entries from {log_path}")
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_hist = subparsers.add_parser("history", help="Show change history for env keys")
    p_hist.add_argument("log", help="Path to history log file")
    p_hist.add_argument("--key", default="", help="Filter by key name")
    p_hist.add_argument("--last", type=int, default=20, help="Show last N entries")
    p_hist.add_argument("--no-color", action="store_true")
    p_hist.set_defaults(func=cmd_history_show)

    p_clear = subparsers.add_parser("history-clear", help="Clear all history entries")
    p_clear.add_argument("log", help="Path to history log file")
    p_clear.set_defaults(func=cmd_history_clear)
