"""Tests for envoy.profiles module."""

import json
import pytest
from pathlib import Path

from envoy.profiles import Profile, ProfileStore, PROFILES_FILE


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / PROFILES_FILE


@pytest.fixture
def store(store_path):
    return ProfileStore.load(store_path)


class TestProfile:
    def test_to_dict_roundtrip(self):
        p = Profile(name="dev", env_path=".env.dev", description="Dev env", tags=["local"])
        restored = Profile.from_dict(p.to_dict())
        assert restored.name == p.name
        assert restored.env_path == p.env_path
        assert restored.tags == p.tags

    def test_defaults(self):
        p = Profile(name="prod", env_path=".env.prod")
        assert p.description == ""
        assert p.tags == []


class TestProfileStore:
    def test_load_empty_when_no_file(self, store_path):
        s = ProfileStore.load(store_path)
        assert s.list_profiles() == []

    def test_add_and_get(self, store):
        p = Profile(name="staging", env_path=".env.staging")
        store.add(p)
        assert store.get("staging") is p

    def test_remove_existing(self, store):
        store.add(Profile(name="dev", env_path=".env.dev"))
        removed = store.remove("dev")
        assert removed is True
        assert store.get("dev") is None

    def test_remove_nonexistent(self, store):
        assert store.remove("ghost") is False

    def test_save_and_reload(self, store_path):
        s = ProfileStore.load(store_path)
        s.add(Profile(name="dev", env_path=".env.dev", tags=["local"]))
        s.save()

        s2 = ProfileStore.load(store_path)
        assert "dev" in s2.profiles
        assert s2.get("dev").tags == ["local"]

    def test_list_profiles(self, store):
        store.add(Profile(name="a", env_path=".env.a"))
        store.add(Profile(name="b", env_path=".env.b"))
        names = [p.name for p in store.list_profiles()]
        assert "a" in names and "b" in names

    def test_find_by_tag(self, store):
        store.add(Profile(name="dev", env_path=".env.dev", tags=["local", "debug"]))
        store.add(Profile(name="prod", env_path=".env.prod", tags=["remote"]))
        results = store.find_by_tag("local")
        assert len(results) == 1
        assert results[0].name == "dev"

    def test_find_by_tag_no_match(self, store):
        store.add(Profile(name="dev", env_path=".env.dev", tags=["local"]))
        assert store.find_by_tag("nonexistent") == []

    def test_overwrite_existing_profile(self, store):
        store.add(Profile(name="dev", env_path=".env.dev"))
        store.add(Profile(name="dev", env_path=".env.dev.new"))
        assert store.get("dev").env_path == ".env.dev.new"
        assert len(store.list_profiles()) == 1
