"""Redaction utilities for masking secret values in .env output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import _is_secret_key

REDACTED_PLACEHOLDER = "***REDACTED***"
PARTIAL_MASK_MIN_LEN = 8


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    def summary(self) -> str:
        count = len(self.redacted_keys)
        if count == 0:
            return "No secrets redacted."
        keys = ", ".join(self.redacted_keys)
        return f"{count} secret(s) redacted: {keys}"


def _partial_mask(value: str) -> str:
    """Show first 2 and last 2 chars, mask the middle."""
    if len(value) < PARTIAL_MASK_MIN_LEN:
        return REDACTED_PLACEHOLDER
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def redact_env(
    env: Dict[str, str],
    *,
    extra_keys: Optional[List[str]] = None,
    partial: bool = False,
) -> RedactResult:
    """Return a RedactResult with secret values masked.

    Args:
        env: Parsed environment dict.
        extra_keys: Additional key names to treat as secrets.
        partial: If True, show partial value instead of full placeholder.
    """
    extra = set(k.upper() for k in (extra_keys or []))
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if _is_secret_key(key) or key.upper() in extra:
            redacted[key] = _partial_mask(value) if partial else REDACTED_PLACEHOLDER
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=redacted_keys,
    )
