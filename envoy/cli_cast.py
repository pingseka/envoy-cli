"""CLI commands for type-casting .env values."""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from envoy.cast import CastType, cast_env
from envoy.parser import parse_env_file


def _colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


_TYPE_MAP: Dict[str, CastType] = {
    "string": CastType.STRING,
    "int": CastType.INTEGER,
    "integer": CastType.INTEGER,
    "float": CastType.FLOAT,
    "bool": CastType.BOOLEAN,
    "boolean": CastType.BOOLEAN,
    "list": CastType.LIST,
}


def _parse_schema_arg(args: list) -> Dict[str, CastType]:
    schema: Dict[str, CastType] = {}
    for item in args:
        if ":" not in item:
            raise argparse.ArgumentTypeError(f"Invalid schema entry {item!r}. Expected KEY:TYPE")
        key, type_str = item.split(":", 1)
        cast_type = _TYPE_MAP.get(type_str.lower())
        if cast_type is None:
            raise argparse.ArgumentTypeError(
                f"Unknown type {type_str!r}. Choose from: {', '.join(_TYPE_MAP)}"
            )
        schema[key] = cast_type
    return schema


def cmd_cast(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(_colored(f"File not found: {args.env_file}", "31"), file=sys.stderr)
        return 1

    try:
        schema = _parse_schema_arg(args.schema)
    except argparse.ArgumentTypeError as exc:
        print(_colored(str(exc), "31"), file=sys.stderr)
        return 1

    result = cast_env(env, schema)

    for entry in result.entries:
        if entry.ok:
            label = _colored("OK", "32")
            print(f"  {label}  {entry}")
        else:
            label = _colored("ERR", "31")
            print(f"  {label}  {entry}", file=sys.stderr)

    if result.has_errors:
        print(_colored(f"\n{len(result.errors())} cast error(s).", "31"), file=sys.stderr)
        return 1

    print(_colored(f"\nAll {len(result.entries)} value(s) cast successfully.", "32"))
    return 0


def register_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("cast", help="Cast .env values to typed Python values")
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument(
        "schema",
        nargs="+",
        metavar="KEY:TYPE",
        help="Key-to-type mappings, e.g. PORT:int DEBUG:bool TAGS:list",
    )
    p.set_defaults(func=cmd_cast)
