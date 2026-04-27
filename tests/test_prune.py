"""Tests for envoy.prune."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy.prune import PruneStatus, prune_env


def _write(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return tmp_dir / ".env"


class TestPruneEnv:
    def test_keeps_unique_keys(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=bar
            BAZ=qux
        """)
        result = prune_env(env_file)
        assert all(e.status == PruneStatus.KEPT for e in result.entries)

    def test_removes_duplicate_key(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=first
            BAR=baz
            FOO=second
        """)
        result = prune_env(env_file)
        dupes = [e for e in result.entries if e.status == PruneStatus.REMOVED_DUPLICATE]
        assert len(dupes) == 1
        assert dupes[0].key == "FOO"

    def test_keeps_first_occurrence_of_duplicate(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=first
            FOO=second
        """)
        prune_env(env_file)
        text = env_file.read_text()
        assert "first" in text
        assert "second" not in text

    def test_removes_empty_values_by_default(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=
            BAR=hello
        """)
        result = prune_env(env_file)
        empty = [e for e in result.entries if e.status == PruneStatus.REMOVED_EMPTY]
        assert len(empty) == 1
        assert empty[0].key == "FOO"

    def test_keeps_empty_values_when_disabled(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=
            BAR=hello
        """)
        result = prune_env(env_file, remove_empty=False)
        assert all(e.status == PruneStatus.KEPT for e in result.entries)

    def test_dry_run_does_not_modify_file(self, env_file: Path) -> None:
        original = "FOO=first\nFOO=second\n"
        env_file.write_text(original)
        prune_env(env_file, dry_run=True)
        assert env_file.read_text() == original

    def test_summary_reports_count(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=a
            FOO=b
            BAR=
        """)
        result = prune_env(env_file)
        assert "2" in result.summary()

    def test_removed_helper_excludes_kept(self, env_file: Path) -> None:
        _write(env_file, """
            FOO=a
            BAR=b
            FOO=c
        """)
        result = prune_env(env_file)
        assert len(result.removed()) == 1
        assert len(result.kept()) == 1
