"""Tag keys in a .env file with arbitrary labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class TagStatus(str, Enum):
    TAGGED = "tagged"
    ALREADY_TAGGED = "already_tagged"
    NOT_FOUND = "not_found"


@dataclass
class TagEntry:
    key: str
    tag: str
    status: TagStatus

    def __str__(self) -> str:
        symbol = {TagStatus.TAGGED: "+", TagStatus.ALREADY_TAGGED: "=", TagStatus.NOT_FOUND: "!"}.get(
            self.status, "?"
        )
        return f"[{symbol}] {self.key} <- {self.tag} ({self.status.value})"


@dataclass
class TagResult:
    entries: List[TagEntry] = field(default_factory=list)
    tags_meta: Dict[str, List[str]] = field(default_factory=dict)  # key -> list of tags

    def tagged(self) -> List[TagEntry]:
        return [e for e in self.entries if e.status == TagStatus.TAGGED]

    def not_found(self) -> List[TagEntry]:
        return [e for e in self.entries if e.status == TagStatus.NOT_FOUND]

    def summary(self) -> str:
        t = len(self.tagged())
        nf = len(self.not_found())
        return f"{t} tagged, {nf} not found"


def tag_keys(
    env_path: str,
    tags: Dict[str, List[str]],
    meta_path: Optional[str] = None,
) -> TagResult:
    """Apply tags to keys in *env_path*.

    *tags* maps each key to a list of tag labels to apply.
    Existing tag metadata is loaded from *meta_path* (a JSON sidecar) if given.
    Returns a TagResult describing what happened.
    """
    import json
    import os

    env = parse_env_file(env_path)
    existing_meta: Dict[str, List[str]] = {}

    if meta_path and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fh:
            existing_meta = json.load(fh)

    result = TagResult(tags_meta=existing_meta)

    for key, labels in tags.items():
        if key not in env:
            for label in labels:
                result.entries.append(TagEntry(key=key, tag=label, status=TagStatus.NOT_FOUND))
            continue
        current = existing_meta.get(key, [])
        for label in labels:
            if label in current:
                result.entries.append(TagEntry(key=key, tag=label, status=TagStatus.ALREADY_TAGGED))
            else:
                current.append(label)
                result.entries.append(TagEntry(key=key, tag=label, status=TagStatus.TAGGED))
        existing_meta[key] = current

    if meta_path:
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(existing_meta, fh, indent=2)

    return result


def keys_for_tag(meta_path: str, tag: str) -> List[str]:
    """Return all keys that carry *tag* according to the sidecar at *meta_path*."""
    import json

    with open(meta_path, "r", encoding="utf-8") as fh:
        meta: Dict[str, List[str]] = json.load(fh)
    return [k for k, labels in meta.items() if tag in labels]
