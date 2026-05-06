"""Integration tests: create then extract an archive and reparse the env."""
import os

import pytest

from envoy.archive import create_archive, extract_archive
from envoy.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envoy\nSECRET_TOKEN=tok123\nDEBUG=true\n")
    return str(p)


class TestArchiveIntegration:
    def test_round_trip_preserves_all_keys(self, env_file, tmp_path):
        original = parse_env_file(env_file)
        arc = str(tmp_path / "snap.zip")
        create_archive(env_file, arc, original)
        dest = str(tmp_path / "restored")
        entry = extract_archive(arc, dest)
        restored = parse_env_file(entry.env_file)
        assert restored == original

    def test_round_trip_preserves_secret_value(self, env_file, tmp_path):
        original = parse_env_file(env_file)
        arc = str(tmp_path / "snap.zip")
        create_archive(env_file, arc, original)
        dest = str(tmp_path / "restored")
        entry = extract_archive(arc, dest)
        restored = parse_env_file(entry.env_file)
        assert restored["SECRET_TOKEN"] == "tok123"

    def test_key_count_in_entry_matches_parsed(self, env_file, tmp_path):
        original = parse_env_file(env_file)
        arc = str(tmp_path / "snap.zip")
        create_entry = create_archive(env_file, arc, original)
        assert create_entry.key_count == len(original)
