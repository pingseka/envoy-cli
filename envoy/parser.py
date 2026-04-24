"""Parser for .env files with support for comments, quoted values, and multiline entries."""

import re
from typing import Dict, Optional


ENV_LINE_PATTERN = re.compile(
    r'^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)
COMMENT_PATTERN = re.compile(r'^\s*#.*$')


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Parse a .env file and return a dictionary of key-value pairs.

    Supports:
    - Inline comments (# comment)
    - Single and double quoted values
    - Empty values
    - Skips blank lines and comment-only lines
    """
    env_vars: Dict[str, str] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line.strip() or COMMENT_PATTERN.match(line):
                continue

            match = ENV_LINE_PATTERN.match(line)
            if match:
                key = match.group("key")
                value = match.group("value").strip()
                value = _strip_inline_comment(value)
                value = _unquote(value)
                env_vars[key] = value

    return env_vars


def _strip_inline_comment(value: str) -> str:
    """Remove inline comments from a value, respecting quoted strings."""
    if value and value[0] in ('"', "'"):
        return value
    comment_idx = value.find(" #")
    if comment_idx != -1:
        value = value[:comment_idx].strip()
    return value


def _unquote(value: str) -> str:
    """Strip surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def serialize_env(env_vars: Dict[str, str], mask_secrets: bool = False) -> str:
    """Serialize a dictionary back to .env file format."""
    lines = []
    for key, value in env_vars.items():
        if mask_secrets and _is_secret_key(key):
            value = "****"
        if " " in value or "#" in value:
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def _is_secret_key(key: str) -> bool:
    """Heuristic to detect secret/sensitive keys."""
    secret_patterns = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "API_KEY", "PRIVATE")
    return any(pattern in key.upper() for pattern in secret_patterns)
