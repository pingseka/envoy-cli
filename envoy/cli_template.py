"""CLI commands for template rendering."""

import argparse
import sys
from typing import List

from envoy.parser import parse_env_file, serialize_env
from envoy.template import render_env


def cmd_render(
    args: argparse.Namespace,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Render an .env file by substituting variable references."""
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        err.write(f"Error: file not found: {args.file}\n")
        return 1

    context = {}
    for item in getattr(args, "var", []) or []:
        if "=" not in item:
            err.write(f"Warning: ignoring malformed --var entry: {item!r}\n")
            continue
        k, v = item.split("=", 1)
        context[k.strip()] = v.strip()

    result = render_env(env, context=context or None)

    if result.has_issues:
        for issue in result.issues:
            err.write(f"Warning: {issue}\n")
        if getattr(args, "strict", False):
            err.write("Aborting: unresolved variables in strict mode.\n")
            return 2

    output = serialize_env(result.rendered)

    if getattr(args, "output", None):
        try:
            with open(args.output, "w") as f:
                f.write(output)
            out.write(f"Rendered env written to {args.output}\n")
        except OSError as exc:
            err.write(f"Error writing output: {exc}\n")
            return 1
    else:
        out.write(output)

    return 0


def register_commands(subparsers) -> None:
    """Register template-related subcommands."""
    render_parser = subparsers.add_parser(
        "render",
        help="Render an .env file with variable substitution",
    )
    render_parser.add_argument("file", help="Path to the .env file")
    render_parser.add_argument(
        "-o", "--output", metavar="FILE", help="Write output to FILE instead of stdout"
    )
    render_parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Extra variable for substitution (repeatable)",
    )
    render_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any variable is unresolved",
    )
    render_parser.set_defaults(func=cmd_render)
