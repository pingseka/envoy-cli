"""Profile management: named sets of environment configurations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PROFILES_FILE = ".envoy_profiles.json"


@dataclass
class Profile:
    name: str
    env_path: str
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "env_path": self.env_path,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            env_path=data["env_path"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class ProfileStore:
    path: Path
    profiles: Dict[str, Profile] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "ProfileStore":
        store = cls(path=path)
        if path.exists():
            data = json.loads(path.read_text())
            for entry in data.get("profiles", []):
                p = Profile.from_dict(entry)
                store.profiles[p.name] = p
        return store

    def save(self) -> None:
        data = {"profiles": [p.to_dict() for p in self.profiles.values()]}
        self.path.write_text(json.dumps(data, indent=2))

    def add(self, profile: Profile) -> None:
        self.profiles[profile.name] = profile

    def remove(self, name: str) -> bool:
        if name in self.profiles:
            del self.profiles[name]
            return True
        return False

    def get(self, name: str) -> Optional[Profile]:
        return self.profiles.get(name)

    def list_profiles(self) -> List[Profile]:
        return list(self.profiles.values())

    def find_by_tag(self, tag: str) -> List[Profile]:
        return [p for p in self.profiles.values() if tag in p.tags]
