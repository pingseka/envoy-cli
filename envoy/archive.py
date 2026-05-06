"""Archive: bundle an env file with metadata into a compressed archive."""
from __future__ import annotations

import json
import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class ArchiveStatus(str, Enum):
    CREATED = "created"
    EXTRACTED = "extracted"
    ERROR = "error"


@dataclass
class ArchiveEntry:
    env_file: str
    archive_path: str
    status: ArchiveStatus
    key_count: int = 0
    message: str = ""

    def __str__(self) -> str:
        return f"[{self.status.value}] {self.env_file} -> {self.archive_path} ({self.key_count} keys)"


@dataclass
class ArchiveResult:
    entries: list[ArchiveEntry] = field(default_factory=list)

    def ok(self) -> bool:
        return all(e.status != ArchiveStatus.ERROR for e in self.entries)

    def summary(self) -> str:
        created = sum(1 for e in self.entries if e.status == ArchiveStatus.CREATED)
        extracted = sum(1 for e in self.entries if e.status == ArchiveStatus.EXTRACTED)
        errors = sum(1 for e in self.entries if e.status == ArchiveStatus.ERROR)
        return f"created={created} extracted={extracted} errors={errors}"


def create_archive(
    env_path: str,
    archive_path: str,
    env_data: Dict[str, str],
    label: Optional[str] = None,
) -> ArchiveEntry:
    """Pack an env file + a JSON metadata sidecar into a zip archive."""
    try:
        meta = {
            "source": os.path.basename(env_path),
            "label": label or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "key_count": len(env_data),
        }
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(env_path, arcname=os.path.basename(env_path))
            zf.writestr("meta.json", json.dumps(meta, indent=2))
        return ArchiveEntry(
            env_file=env_path,
            archive_path=archive_path,
            status=ArchiveStatus.CREATED,
            key_count=len(env_data),
        )
    except Exception as exc:  # pragma: no cover
        return ArchiveEntry(
            env_file=env_path,
            archive_path=archive_path,
            status=ArchiveStatus.ERROR,
            message=str(exc),
        )


def extract_archive(archive_path: str, dest_dir: str) -> ArchiveEntry:
    """Unpack an archive created by create_archive into dest_dir."""
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            zf.extractall(dest_dir)
            meta_raw = zf.read("meta.json") if "meta.json" in names else b"{}"
        meta = json.loads(meta_raw)
        key_count = int(meta.get("key_count", 0))
        env_name = meta.get("source", "")
        return ArchiveEntry(
            env_file=os.path.join(dest_dir, env_name),
            archive_path=archive_path,
            status=ArchiveStatus.EXTRACTED,
            key_count=key_count,
        )
    except Exception as exc:  # pragma: no cover
        return ArchiveEntry(
            env_file="",
            archive_path=archive_path,
            status=ArchiveStatus.ERROR,
            message=str(exc),
        )
