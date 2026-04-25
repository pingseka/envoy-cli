"""Tests for envoy.cli_history commands."""
import argparse
import pytest
from pathlib import Path
from envoy.history import HistoryLog
from envoy.cli_history import cmd_history_show, cmd_history_clear


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "history.json"


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"key": "", "last": 20, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _populate_log(log_path: Path) -> HistoryLog:
    log = HistoryLog(path=log_path)
    log.load()
    log.record("set", "DB_URL", new_value="postgres://localhost", author="alice")
    log.record("set", "API_SECRET", new_value="topsecret", author="bob")
    log.record("delete", "OLD_KEY", old_value="legacy")
    log.save()
    return log


class TestCmdHistoryShow:
    def test_shows_all_entries_by_default(self, log_path, capsys):
        _populate_log(log_path)
        args = make_args(log=str(log_path))
        rc = cmd_history_show(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "DB_URL" in out
        assert "API_SECRET" in out
        assert "OLD_KEY" in out

    def test_filters_by_key(self, log_path, capsys):
        _populate_log(log_path)
        args = make_args(log=str(log_path), key="DB_URL")
        cmd_history_show(args)
        out = capsys.readouterr().out
        assert "DB_URL" in out
        assert "OLD_KEY" not in out

    def test_masks_secret_values(self, log_path, capsys):
        _populate_log(log_path)
        args = make_args(log=str(log_path), key="API_SECRET")
        cmd_history_show(args)
        out = capsys.readouterr().out
        assert "topsecret" not in out
        assert "***" in out

    def test_does_not_mask_non_secret(self, log_path, capsys):
        _populate_log(log_path)
        args = make_args(log=str(log_path), key="DB_URL")
        cmd_history_show(args)
        out = capsys.readouterr().out
        assert "postgres://localhost" in out

    def test_shows_author(self, log_path, capsys):
        _populate_log(log_path)
        args = make_args(log=str(log_path), key="DB_URL")
        cmd_history_show(args)
        out = capsys.readouterr().out
        assert "alice" in out

    def test_empty_log_prints_message(self, log_path, capsys):
        args = make_args(log=str(log_path))
        rc = cmd_history_show(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "No history" in out

    def test_last_limits_output(self, log_path, capsys):
        log = HistoryLog(path=log_path)
        log.load()
        for i in range(10):
            log.record("set", f"KEY_{i}", new_value=str(i))
        log.save()
        args = make_args(log=str(log_path), last=3)
        cmd_history_show(args)
        out = capsys.readouterr().out
        lines = [l for l in out.strip().splitlines() if l]
        assert len(lines) == 3


class TestCmdHistoryClear:
    def test_clears_entries_and_saves(self, log_path, capsys):
        _populate_log(log_path)
        args = argparse.Namespace(log=str(log_path))
        rc = cmd_history_clear(args)
        assert rc == 0
        log = HistoryLog(path=log_path)
        log.load()
        assert log.entries == []

    def test_prints_count_cleared(self, log_path, capsys):
        _populate_log(log_path)
        args = argparse.Namespace(log=str(log_path))
        cmd_history_clear(args)
        out = capsys.readouterr().out
        assert "3" in out
