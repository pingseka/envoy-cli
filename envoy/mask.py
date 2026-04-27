"""Mask module: selectively mask values in env files by key pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env, _is_secret_key


class MaskStatus(str, Enum):
    MASKED = "masked"
    SKIPPED = "skipped"
    NOT_FOUND = "not_found"


@dataclass
class MaskEntry:
    key: str
    status: MaskStatus
    original: Optional[str] = None

    def __str__(self) -> str:
        if self.status == MaskStatus.MASKED:
            return f"[masked]  {self.key}"
        if self.status == MaskStatus.SKIPPED:
            return f"[skipped] {self.key}"
        return f"[missing] {self.key}"


@dataclass
class MaskResult:
    entries: List[MaskEntry] = field(default_factory=list)
    masked_env: Dict[str, str] = field(default_factory=dict)

    @property
    def masked_count(self) -> int:
        return sum(1 for e in self.entries if e.status == MaskStatus.MASKED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.entries if e.status == MaskStatus.SKIPPED)

    def summary(self) -> str:
        return f"{self.masked_count} masked, {self.skipped_count} skipped"


MASK_PLACEHOLDER = "***"


def mask_env(
    env_path: str,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    auto_secrets: bool = False,
) -> MaskResult:
    """Mask specified keys in an env file, returning a MaskResult."""
    env = parse_env_file(env_path)
    masked_env = dict(env)
    entries: List[MaskEntry] = []
    masked_keys: set = set()

    explicit_keys = list(keys or [])

    if pattern:
        rx = re.compile(pattern)
        for k in env:
            if rx.search(k):
                explicit_keys.append(k)

    if auto_secrets:
        for k in env:
            if _is_secret_key(k):
                explicit_keys.append(k)

    for key in dict.fromkeys(explicit_keys):  # deduplicate, preserve order
        if key not in env:
            entries.append(MaskEntry(key=key, status=MaskStatus.NOT_FOUND))
        else:
            masked_env[key] = MASK_PLACEHOLDER
            masked_keys.add(key)
            entries.append(MaskEntry(key=key, status=MaskStatus.MASKED, original=env[key]))

    for key in env:
        if key not in masked_keys and key not in {e.key for e in entries}:
            entries.append(MaskEntry(key=key, status=MaskStatus.SKIPPED))

    return MaskResult(entries=entries, masked_env=masked_env)
