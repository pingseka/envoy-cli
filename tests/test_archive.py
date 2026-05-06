"""Tests for envoy.archive module."""
import json
import os
import zipfile

import pytest

from envoy.archive import (
    ArchiveStatus,
    ArchiveEntry,
    ArchiveResult,
    create_archive,
    extract_archive,
)


@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def env_file(tmp_dir):
    p = tmp_dir / ".env"
    p.write_text("FOO=bar\nSECRET_KEY=abc123\n")
    return str(p)


@pytest.fixture()
def archive_path(tmp_dir):
    return str(tmp_dir / "backup.zip")


class TestCreateArchive:
    def test_creates_zip_file(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {"FOO": "bar"})
        assert os.path.isfile(archive_path)

    def test_status_is_created(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {"FOO": "bar"})
        assert entry.status == ArchiveStatus.CREATED

    def test_key_count_matches(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {"FOO": "bar", "BAZ": "qux"})
        assert entry.key_count == 2

    def test_zip_contains_env_file(self, env_file, archive_path):
        create_archive(env_file, archive_path, {})
        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
        assert ".env" in names

    def test_zip_contains_meta_json(self, env_file, archive_path):
        create_archive(env_file, archive_path, {})
        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
        assert "meta.json" in names

    def test_meta_json_has_label(self, env_file, archive_path):
        create_archive(env_file, archive_path, {}, label="production")
        with zipfile.ZipFile(archive_path) as zf:
            meta = json.loads(zf.read("meta.json"))
        assert meta["label"] == "production"

    def test_str_includes_status(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {})
        assert "created" in str(entry)


class TestExtractArchive:
    def test_extracts_env_file(self, env_file, archive_path, tmp_dir):
        create_archive(env_file, archive_path, {"FOO": "bar"})
        dest = str(tmp_dir / "out")
        entry = extract_archive(archive_path, dest)
        assert os.path.isfile(entry.env_file)

    def test_status_is_extracted(self, env_file, archive_path, tmp_dir):
        create_archive(env_file, archive_path, {})
        dest = str(tmp_dir / "out")
        entry = extract_archive(archive_path, dest)
        assert entry.status == ArchiveStatus.EXTRACTED

    def test_key_count_from_meta(self, env_file, archive_path, tmp_dir):
        create_archive(env_file, archive_path, {"A": "1", "B": "2", "C": "3"})
        dest = str(tmp_dir / "out")
        entry = extract_archive(archive_path, dest)
        assert entry.key_count == 3

    def test_str_includes_extracted(self, env_file, archive_path, tmp_dir):
        create_archive(env_file, archive_path, {})
        dest = str(tmp_dir / "out")
        entry = extract_archive(archive_path, dest)
        assert "extracted" in str(entry)


class TestArchiveResult:
    def test_ok_when_no_errors(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {})
        result = ArchiveResult(entries=[entry])
        assert result.ok()

    def test_summary_shows_counts(self, env_file, archive_path):
        entry = create_archive(env_file, archive_path, {})
        result = ArchiveResult(entries=[entry])
        assert "created=1" in result.summary()
