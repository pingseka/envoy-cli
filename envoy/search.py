"""Search env files by key pattern, value pattern, or both."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import _is_secret_key


@dataclass
class SearchMatch:
    key: str
    value: str
    is_secret: bool = False

    def display_value(self) -> str:
        return "***" if self.is_secret else self.value

    def __str__(self) -> str:
        return f"{self.key}={self.display_value()}"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)
    total_scanned: int = 0

    @property
    def match_count(self) -> int:
        return len(self.matches)

    def summary(self) -> str:
        return (
            f"{self.match_count} match(es) found in "
            f"{self.total_scanned} key(s) scanned"
        )


def search_env(
    env: Dict[str, str],
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search env dict by key and/or value regex patterns."""
    if not key_pattern and not value_pattern:
        raise ValueError("At least one of key_pattern or value_pattern must be given")

    flags = 0 if case_sensitive else re.IGNORECASE
    key_re = re.compile(key_pattern, flags) if key_pattern else None
    val_re = re.compile(value_pattern, flags) if value_pattern else None

    matches: List[SearchMatch] = []
    for key, value in env.items():
        key_ok = key_re.search(key) is not None if key_re else True
        val_ok = val_re.search(value) is not None if val_re else True
        if key_ok and val_ok:
            matches.append(SearchMatch(key=key, value=value, is_secret=_is_secret_key(key)))

    return SearchResult(matches=matches, total_scanned=len(env))
