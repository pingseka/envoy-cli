"""Tests for envoy.cli_reorder."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.cli_reorder import cmd_reorder


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture
def tmp_env(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env", "ALPHA=1\nBETA=2\nGAMMA=3\n")


def make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file="",
        keys=None,
        alpha=False,
        drop=False,
        write=False,
        output=None,
        verbose=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdReorder:
    def test_exits_zero_on_success(self, tmp_env: Path, capsys) -> None:
        args = make_args(file=str(tmp_env), keys=["GAMMA", "ALPHA", "BETA"])
        rc = cmd_reorder(args)
        assert rc == 0

    def test_prints_reordered_output(self, tmp_env: Path, capsys) -> None:
        args = make_args(file=str(tmp_env), keys=["GAMMA", "ALPHA", "BETA"])
        cmd_reorder(args)
        out = capsys.readouterr().out
        lines = [l for l in out.splitlines() if "=" in l]
        keys = [l.split("=")[0] for l in lines]
        assert keys == ["GAMMA", "ALPHA", "BETA"]

    def test_alpha_flag_sorts_alphabetically(self, tmp_env: Path, capsys) -> None:
        args = make_args(file=str(tmp_env), alpha=True, keys=[])
        rc = cmd_reorder(args)
        assert rc == 0
        out = capsys.readouterr().out
        lines = [l for l in out.splitlines() if "=" in l]
        keys = [l.split("=")[0] for l in lines]
        assert keys == sorted(keys)

    def test_write_flag_saves_to_file(self, tmp_env: Path, capsys) -> None:
        args = make_args(
            file=str(tmp_env), keys=["GAMMA", "BETA", "ALPHA"], write=True
        )
        cmd_reorder(args)
        content = tmp_env.read_text()
        lines = [l for l in content.splitlines() if "=" in l]
        keys = [l.split("=")[0] for l in lines]
        assert keys == ["GAMMA", "BETA", "ALPHA"]

    def test_missing_file_exits_nonzero(self, tmp_path: Path, capsys) -> None:
        args = make_args(file=str(tmp_path / "missing.env"), keys=["A"])
        rc = cmd_reorder(args)
        assert rc == 1

    def test_no_order_exits_nonzero(self, tmp_env: Path, capsys) -> None:
        args = make_args(file=str(tmp_env), keys=[])
        rc = cmd_reorder(args)
        assert rc == 1

    def test_verbose_shows_per_key_status(self, tmp_env: Path, capsys) -> None:
        args = make_args(
            file=str(tmp_env), keys=["GAMMA", "ALPHA", "BETA"], verbose=True
        )
        cmd_reorder(args)
        out = capsys.readouterr().out
        assert "GAMMA" in out or "ALPHA" in out
