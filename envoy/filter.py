"""Filter env vars by key pattern, value pattern, or secret status."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import _is_secret_key


@dataclass
class FilterResult:
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.matched) + len(self.excluded)

    @property
    def matched_count(self) -> int:
        return len(self.matched)

    def summary(self) -> str:
        return (
            f"{self.matched_count} matched, "
            f"{len(self.excluded)} excluded "
            f"(total {self.total})"
        )


def filter_env(
    env: Dict[str, str],
    *,
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    secrets_only: bool = False,
    non_secrets_only: bool = False,
    keys: Optional[List[str]] = None,
) -> FilterResult:
    """Return a FilterResult partitioning *env* into matched/excluded.

    Filters are ANDed together — a key must satisfy all supplied criteria
    to appear in ``matched``.
    """
    if secrets_only and non_secrets_only:
        raise ValueError("secrets_only and non_secrets_only are mutually exclusive")

    key_re = re.compile(key_pattern) if key_pattern else None
    val_re = re.compile(value_pattern) if value_pattern else None
    key_set = set(keys) if keys else None

    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for k, v in env.items():
        if key_re and not key_re.search(k):
            excluded[k] = v
            continue
        if val_re and not val_re.search(v):
            excluded[k] = v
            continue
        if secrets_only and not _is_secret_key(k):
            excluded[k] = v
            continue
        if non_secrets_only and _is_secret_key(k):
            excluded[k] = v
            continue
        if key_set is not None and k not in key_set:
            excluded[k] = v
            continue
        matched[k] = v

    return FilterResult(matched=matched, excluded=excluded)
