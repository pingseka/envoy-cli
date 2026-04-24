"""Tests for envoy.cli_snapshot commands."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from envoy.cli_snapshot import (
    cmd_snapshot_capture,
    cmd_snapshot_list,
    cmd_snapshot_remove,
    cmd_snapshot_restore,
)
from envoy.snapshot import SnapshotStore


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=value\nSECRET_TOKEN=s3cr3t\n")
    return str(p)


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "snaps.json")


def make_args(**kwargs):
    return SimpleNamespace(**kwargs)


class TestCmdSnapshotCapture:
    def test_captures_and_prints(self, tmp_env, store_path, capsys):
        args = make_args(env_file=tmp_env, label="v1", store=store_path)
        cmd_snapshot_capture(args)
        out = capsys.readouterr().out
        assert "v1" in out
        assert "captured" in out.lower()

    def test_snapshot_persisted(self, tmp_env, store_path):
        args = make_args(env_file=tmp_env, label="persist", store=store_path)
        cmd_snapshot_capture(args)
        store = SnapshotStore(store_path=Path(store_path))
        store.load()
        assert store.get("persist") is not None


class TestCmdSnapshotList:
    def test_empty_store(self, store_path, capsys):
        args = make_args(store=store_path)
        cmd_snapshot_list(args)
        out = capsys.readouterr().out
        assert "No snapshots" in out

    def test_lists_captured_snapshots(self, tmp_env, store_path, capsys):
        cap_args = make_args(env_file=tmp_env, label="listed", store=store_path)
        cmd_snapshot_capture(cap_args)
        list_args = make_args(store=store_path)
        cmd_snapshot_list(list_args)
        out = capsys.readouterr().out
        assert "listed" in out


class TestCmdSnapshotRestore:
    def test_restore_to_output(self, tmp_env, store_path, tmp_path, capsys):
        cap_args = make_args(env_file=tmp_env, label="snap", store=store_path)
        cmd_snapshot_capture(cap_args)
        out_file = str(tmp_path / "out.env")
        res_args = make_args(label="snap", output=out_file, store=store_path)
        cmd_snapshot_restore(res_args)
        assert Path(out_file).exists()
        assert "KEY" in Path(out_file).read_text()

    def test_restore_missing_label_exits(self, store_path):
        args = make_args(label="ghost", output=None, store=store_path)
        with pytest.raises(SystemExit):
            cmd_snapshot_restore(args)


class TestCmdSnapshotRemove:
    def test_remove_existing(self, tmp_env, store_path, capsys):
        cap_args = make_args(env_file=tmp_env, label="del", store=store_path)
        cmd_snapshot_capture(cap_args)
        rm_args = make_args(label="del", store=store_path)
        cmd_snapshot_remove(rm_args)
        out = capsys.readouterr().out
        assert "removed" in out.lower()

    def test_remove_nonexistent_exits(self, store_path):
        args = make_args(label="nope", store=store_path)
        with pytest.raises(SystemExit):
            cmd_snapshot_remove(args)
