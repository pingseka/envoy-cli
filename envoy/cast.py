"""Type casting utilities for .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CastType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"


@dataclass
class CastEntry:
    key: str
    raw: str
    cast_type: CastType
    value: Any
    ok: bool
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.ok:
            return f"{self.key}: {self.raw!r} -> ({self.cast_type.value}) {self.value!r}"
        return f"{self.key}: {self.raw!r} -> ERROR: {self.error}"


@dataclass
class CastResult:
    entries: List[CastEntry] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(not e.ok for e in self.entries)

    @property
    def values(self) -> Dict[str, Any]:
        return {e.key: e.value for e in self.entries if e.ok}

    def errors(self) -> List[CastEntry]:
        return [e for e in self.entries if not e.ok]


_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


def _cast_value(raw: str, cast_type: CastType) -> Any:
    if cast_type == CastType.STRING:
        return raw
    if cast_type == CastType.INTEGER:
        return int(raw)
    if cast_type == CastType.FLOAT:
        return float(raw)
    if cast_type == CastType.BOOLEAN:
        lower = raw.strip().lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        raise ValueError(f"Cannot convert {raw!r} to boolean")
    if cast_type == CastType.LIST:
        return [item.strip() for item in raw.split(",") if item.strip()]
    raise ValueError(f"Unknown cast type: {cast_type}")


def cast_env(env: Dict[str, str], schema: Dict[str, CastType]) -> CastResult:
    """Cast env values according to a schema mapping key -> CastType."""
    result = CastResult()
    for key, cast_type in schema.items():
        raw = env.get(key, "")
        try:
            value = _cast_value(raw, cast_type)
            result.entries.append(CastEntry(key=key, raw=raw, cast_type=cast_type, value=value, ok=True))
        except (ValueError, TypeError) as exc:
            result.entries.append(
                CastEntry(key=key, raw=raw, cast_type=cast_type, value=None, ok=False, error=str(exc))
            )
    return result
