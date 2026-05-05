"""Apply a set of key-value patches (add/update/delete) to an env mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class PatchOp(str, Enum):
    SET = "set"
    DELETE = "delete"


@dataclass
class PatchEntry:
    key: str
    op: PatchOp
    old_value: Optional[str]
    new_value: Optional[str]

    def __str__(self) -> str:
        if self.op == PatchOp.DELETE:
            return f"[-] {self.key} (deleted)"
        if self.old_value is None:
            return f"[+] {self.key}={self.new_value}"
        return f"[~] {self.key}: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class PatchResult:
    entries: List[PatchEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> List[PatchEntry]:
        return [e for e in self.entries if e.op == PatchOp.SET and e.old_value != e.new_value]

    @property
    def deleted(self) -> List[PatchEntry]:
        return [e for e in self.entries if e.op == PatchOp.DELETE]

    @property
    def added(self) -> List[PatchEntry]:
        return [e for e in self.entries if e.op == PatchOp.SET and e.old_value is None]

    def summary(self) -> str:
        return (
            f"{len(self.added)} added, {len(self.changed)} updated, "
            f"{len(self.deleted)} deleted"
        )


def patch_env(
    env_path: str,
    patches: Dict[str, Optional[str]],
) -> PatchResult:
    """Apply patches to an env file.

    A patch value of ``None`` means delete the key.
    Returns a PatchResult with the updated env mapping and a log of changes.
    """
    original: Dict[str, str] = parse_env_file(env_path)
    result_env: Dict[str, str] = dict(original)
    entries: List[PatchEntry] = []

    for key, value in patches.items():
        if value is None:
            old = result_env.pop(key, None)
            if old is not None:
                entries.append(PatchEntry(key=key, op=PatchOp.DELETE, old_value=old, new_value=None))
        else:
            old = result_env.get(key)
            result_env[key] = value
            entries.append(PatchEntry(key=key, op=PatchOp.SET, old_value=old, new_value=value))

    return PatchResult(entries=entries, env=result_env)
