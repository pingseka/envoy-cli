"""Rename keys across a .env file with optional dry-run support."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envoy.parser import parse_env_file, serialize_env


@dataclass
class RenameEntry:
    old_key: str
    new_key: str
    value: str
    skipped: bool = False
    skip_reason: Optional[str] = None

    def __str__(self) -> str:
        if self.skipped:
            return f"SKIP  {self.old_key} -> {self.new_key} ({self.skip_reason})"
        return f"RENAME {self.old_key} -> {self.new_key}"


@dataclass
class RenameResult:
    entries: List[RenameEntry] = field(default_factory=list)
    renamed: int = 0
    skipped: int = 0

    def has_renames(self) -> bool:
        return self.renamed > 0

    def summary(self) -> str:
        return f"{self.renamed} renamed, {self.skipped} skipped"


def rename_keys(
    env_file: str,
    renames: Dict[str, str],
    dry_run: bool = False,
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in an env file.

    Args:
        env_file: Path to the .env file.
        renames: Mapping of old_key -> new_key.
        dry_run: If True, do not write changes to disk.
        overwrite: If True, allow renaming even if new_key already exists.

    Returns:
        RenameResult with details of each rename operation.
    """
    data = parse_env_file(env_file)
    result = RenameResult()
    updated = dict(data)

    for old_key, new_key in renames.items():
        if old_key not in data:
            entry = RenameEntry(
                old_key=old_key,
                new_key=new_key,
                value="",
                skipped=True,
                skip_reason="key not found",
            )
            result.entries.append(entry)
            result.skipped += 1
            continue

        if new_key in data and not overwrite:
            entry = RenameEntry(
                old_key=old_key,
                new_key=new_key,
                value=data[old_key],
                skipped=True,
                skip_reason=f"target key '{new_key}' already exists",
            )
            result.entries.append(entry)
            result.skipped += 1
            continue

        value = updated.pop(old_key)
        updated[new_key] = value
        entry = RenameEntry(old_key=old_key, new_key=new_key, value=value)
        result.entries.append(entry)
        result.renamed += 1

    if not dry_run and result.renamed > 0:
        serialize_env(updated, env_file)

    return result
