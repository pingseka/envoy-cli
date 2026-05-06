"""Tests for envoy.cli_archive commands."""
import os
import types
import zipfile

import pytest

from envoy.cli_archive import cmd_archive_create, cmd_archive_extract


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nDB_PASSWORD=secret\n")
    return str(p)


def make_args(**kwargs):
    ns = types.SimpleNamespace(**kwargs)
    return ns


class TestCmdArchiveCreate:
    def test_exits_zero_on_success(self, tmp_env, tmp_path):
        out = str(tmp_path / "out.zip")
        args = make_args(env_file=tmp_env, output=out, label="")
        assert cmd_archive_create(args) == 0

    def test_creates_zip_file(self, tmp_env, tmp_path):
        out = str(tmp_path / "out.zip")
        args = make_args(env_file=tmp_env, output=out, label="")
        cmd_archive_create(args)
        assert os.path.isfile(out)

    def test_zip_is_valid(self, tmp_env, tmp_path):
        out = str(tmp_path / "out.zip")
        args = make_args(env_file=tmp_env, output=out, label="")
        cmd_archive_create(args)
        assert zipfile.is_zipfile(out)

    def test_exits_one_when_file_missing(self, tmp_path):
        out = str(tmp_path / "out.zip")
        args = make_args(env_file=str(tmp_path / "missing.env"), output=out, label="")
        assert cmd_archive_create(args) == 1

    def test_label_stored_in_meta(self, tmp_env, tmp_path):
        import json
        out = str(tmp_path / "out.zip")
        args = make_args(env_file=tmp_env, output=out, label="staging")
        cmd_archive_create(args)
        with zipfile.ZipFile(out) as zf:
            meta = json.loads(zf.read("meta.json"))
        assert meta["label"] == "staging"


class TestCmdArchiveExtract:
    def test_exits_zero_on_success(self, tmp_env, tmp_path):
        arc = str(tmp_path / "out.zip")
        cmd_archive_create(make_args(env_file=tmp_env, output=arc, label=""))
        dest = str(tmp_path / "extracted")
        args = make_args(archive=arc, dest=dest)
        assert cmd_archive_extract(args) == 0

    def test_env_file_exists_after_extract(self, tmp_env, tmp_path):
        arc = str(tmp_path / "out.zip")
        cmd_archive_create(make_args(env_file=tmp_env, output=arc, label=""))
        dest = str(tmp_path / "extracted")
        args = make_args(archive=arc, dest=dest)
        cmd_archive_extract(args)
        assert os.path.isfile(os.path.join(dest, ".env"))

    def test_extracted_content_matches_original(self, tmp_env, tmp_path):
        arc = str(tmp_path / "out.zip")
        cmd_archive_create(make_args(env_file=tmp_env, output=arc, label=""))
        dest = str(tmp_path / "extracted")
        cmd_archive_extract(make_args(archive=arc, dest=dest))
        with open(os.path.join(dest, ".env")) as f:
            content = f.read()
        assert "FOO=bar" in content
