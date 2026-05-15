"""Tests for the CLI dispatcher."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from codemonkeys.cli import (
    _build_parser,
    _get_diff_files,
    _resolve_max_parallel,
    main,
)


# ---------------------------------------------------------------------------
# _build_parser — review
# ---------------------------------------------------------------------------


def test_parser_review_command_exists() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "**/*.py"])
    assert args.command == "review"
    assert args.patterns == ["**/*.py"]


def test_parser_review_diff_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "--diff"])
    assert args.diff is True


def test_parser_review_max_parallel() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "--max-parallel", "8", "**/*.py"])
    assert args.max_parallel == 8


def test_parser_review_quiet_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "--quiet", "--diff"])
    assert args.quiet is True


def test_parser_no_command_exits() -> None:
    with pytest.raises(SystemExit):
        main([])


# ---------------------------------------------------------------------------
# _build_parser — edit
# ---------------------------------------------------------------------------


def test_parser_edit_command_exists() -> None:
    parser = _build_parser()
    args = parser.parse_args(["edit", "foo.py", "--task", "fix it"])
    assert args.command == "edit"
    assert args.file_paths == ["foo.py"]
    assert args.task == "fix it"
    assert args.task_type == "fix"


def test_parser_edit_multi_file() -> None:
    parser = _build_parser()
    args = parser.parse_args(["edit", "a.py", "b.py", "--task", "refactor"])
    assert args.file_paths == ["a.py", "b.py"]


def test_parser_edit_findings() -> None:
    parser = _build_parser()
    args = parser.parse_args(["edit", "foo.py", "--findings", "1,3,5"])
    assert args.findings == "1,3,5"


# ---------------------------------------------------------------------------
# _build_parser — implement
# ---------------------------------------------------------------------------


def test_parser_implement_command_exists() -> None:
    parser = _build_parser()
    args = parser.parse_args(["implement", "new.py", "--task", "add feature"])
    assert args.command == "implement"
    assert args.file_paths == ["new.py"]
    assert args.task_type == "feat"


def test_parser_implement_task_file() -> None:
    parser = _build_parser()
    args = parser.parse_args(["implement", "new.py", "--task-file", "plan.md"])
    assert args.task_file == "plan.md"


# ---------------------------------------------------------------------------
# _resolve_max_parallel
# ---------------------------------------------------------------------------


def test_resolve_max_parallel_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEMONKEYS_MAX_PARALLEL_AGENTS", "16")
    assert _resolve_max_parallel(8) == 8


def test_resolve_max_parallel_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEMONKEYS_MAX_PARALLEL_AGENTS", "16")
    assert _resolve_max_parallel(None) == 16


def test_resolve_max_parallel_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODEMONKEYS_MAX_PARALLEL_AGENTS", raising=False)
    assert _resolve_max_parallel(None) == 4


# ---------------------------------------------------------------------------
# _get_diff_files
# ---------------------------------------------------------------------------


@patch("codemonkeys.cli.subprocess.run")
def test_get_diff_files_returns_changed_files(mock_run) -> None:
    mock_run.side_effect = [
        type("R", (), {"returncode": 0, "stdout": "refs/remotes/origin/main\n"})(),
        type("R", (), {"stdout": "foo.py\nbar.js\nREADME.md\n"})(),
    ]
    result = _get_diff_files()
    assert result == ["foo.py", "bar.js", "README.md"]


# ---------------------------------------------------------------------------
# main — review
# ---------------------------------------------------------------------------


def test_main_no_patterns_no_diff_exits() -> None:
    with pytest.raises(SystemExit):
        main(["review"])


@patch("codemonkeys.cli.discover_files", return_value=[])
def test_main_no_files_found_exits(mock_discover) -> None:
    with pytest.raises(SystemExit):
        main(["review", "nonexistent/**/*.py"])


@patch("codemonkeys.cli.get_reviewer", return_value=None)
@patch("codemonkeys.cli.discover_files", return_value=["foo.xyz"])
def test_main_no_reviewer_for_extension_exits(mock_discover, mock_get) -> None:
    with pytest.raises(SystemExit):
        main(["review", "**/*.xyz"])


# ---------------------------------------------------------------------------
# main — edit / implement require task
# ---------------------------------------------------------------------------


def test_main_edit_no_task_exits() -> None:
    with pytest.raises(SystemExit):
        main(["edit", "foo.py"])


def test_main_implement_no_task_exits() -> None:
    with pytest.raises(SystemExit):
        main(["implement", "foo.py"])


