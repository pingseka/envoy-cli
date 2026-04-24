"""Export .env file contents to various formats (shell, JSON, dotenv)."""

import json
from typing import Dict, Optional
from envoy.parser import _is_secret_key

SUPPORTED_FORMATS = ("dotenv", "shell", "json")


def export_env(
    env: Dict[str, str],
    fmt: str = "dotenv",
    mask_secrets: bool = False,
    mask_value: str = "****",
) -> str:
    """Serialize an env dict to the requested format string.

    Args:
        env: Mapping of key -> value.
        fmt: One of 'dotenv', 'shell', or 'json'.
        mask_secrets: Replace secret values with *mask_value*.
        mask_value: Placeholder used when masking.

    Returns:
        A string representation in the chosen format.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    resolved = {
        k: (mask_value if mask_secrets and _is_secret_key(k) else v)
        for k, v in env.items()
    }

    if fmt == "json":
        return json.dumps(resolved, indent=2)

    lines = []
    for key, value in resolved.items():
        # Quote values that contain spaces or special shell characters
        needs_quoting = any(c in value for c in (" ", "\t", "'", '"', "$", "`", "\\"))
        quoted_value = f'"{value}"' if needs_quoting else value

        if fmt == "shell":
            lines.append(f"export {key}={quoted_value}")
        else:  # dotenv
            lines.append(f"{key}={quoted_value}")

    return "\n".join(lines)


def export_to_file(
    env: Dict[str, str],
    path: str,
    fmt: str = "dotenv",
    mask_secrets: bool = False,
) -> None:
    """Write exported env content to *path*."""
    content = export_env(env, fmt=fmt, mask_secrets=mask_secrets)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")
