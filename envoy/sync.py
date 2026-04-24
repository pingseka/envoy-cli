"""Sync .env files across environments, merging keys with conflict detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envoy.parser import parse_env_file, serialize_env


class SyncConflict(Enum):
    MISSING_IN_TARGET = "missing_in_target"
    MISSING_IN_SOURCE = "missing_in_source"
    VALUE_DIFFERS = "value_differs"


@dataclass
class SyncIssue:
    key: str
    conflict: SyncConflict
    source_value: Optional[str] = None
    target_value: Optional[str] = None

    def __str__(self) -> str:
        if self.conflict == SyncConflict.MISSING_IN_TARGET:
            return f"  [+] {self.key} (missing in target)"
        if self.conflict == SyncConflict.MISSING_IN_SOURCE:
            return f"  [-] {self.key} (missing in source)"
        return f"  [~] {self.key} (value differs)"


@dataclass
class SyncResult:
    source_path: Path
    target_path: Path
    issues: List[SyncIssue] = field(default_factory=list)
    merged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        lines = [
            f"Sync: {self.source_path} -> {self.target_path}",
            f"  {len(self.merged)} keys in result, {len(self.issues)} issue(s)",
        ]
        for issue in self.issues:
            lines.append(str(issue))
        return "\n".join(lines)


def sync_env_files(
    source: Path,
    target: Path,
    overwrite: bool = False,
    add_missing: bool = True,
) -> SyncResult:
    """Merge source env into target env, returning a SyncResult.

    Args:
        source: Path to the authoritative source .env file.
        target: Path to the target .env file to sync into.
        overwrite: If True, source values overwrite differing target values.
        add_missing: If True, keys in source but absent in target are added.
    """
    src_env = parse_env_file(source)
    tgt_env = parse_env_file(target)

    issues: List[SyncIssue] = []
    merged = dict(tgt_env)

    for key, src_val in src_env.items():
        if key not in tgt_env:
            issues.append(SyncIssue(key, SyncConflict.MISSING_IN_TARGET, source_value=src_val))
            if add_missing:
                merged[key] = src_val
        elif tgt_env[key] != src_val:
            issues.append(
                SyncIssue(key, SyncConflict.VALUE_DIFFERS, source_value=src_val, target_value=tgt_env[key])
            )
            if overwrite:
                merged[key] = src_val

    for key in tgt_env:
        if key not in src_env:
            issues.append(SyncIssue(key, SyncConflict.MISSING_IN_SOURCE, target_value=tgt_env[key]))

    return SyncResult(source_path=source, target_path=target, issues=issues, merged=merged)


def write_synced_env(result: SyncResult) -> None:
    """Write the merged env back to the target path."""
    result.target_path.write_text(serialize_env(result.merged))
