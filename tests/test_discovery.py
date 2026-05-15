"""Characterization tests for codemonkeys/core/discovery.py."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from codemonkeys.core.discovery import batch, discover_files


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------


def test_batch_empty() -> None:
    assert batch([]) == []


def test_batch_default_size_of_3() -> None:
    assert batch(["a", "b", "c"]) == [["a", "b", "c"]]


def test_batch_splits_evenly() -> None:
    assert batch(["a", "b", "c", "d", "e", "f"], size=3) == [
        ["a", "b", "c"],
        ["d", "e", "f"],
    ]


def test_batch_partial_last_chunk() -> None:
    assert batch(["a", "b", "c", "d"], size=3) == [["a", "b", "c"], ["d"]]


def test_batch_size_one() -> None:
    assert batch(["x", "y"], size=1) == [["x"], ["y"]]


def test_batch_size_larger_than_list() -> None:
    assert batch(["a", "b"], size=10) == [["a", "b"]]


def test_batch_single_item() -> None:
    assert batch(["only"], size=3) == [["only"]]


def test_batch_size_equals_list_length() -> None:
    assert batch(["a", "b", "c"], size=3) == [["a", "b", "c"]]


# ---------------------------------------------------------------------------
# discover_files
# ---------------------------------------------------------------------------


def _mock_run(stdout: str) -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    return m


def test_discover_files_returns_sorted_results() -> None:
    with patch("subprocess.run", return_value=_mock_run("b.py\na.py\nc.py\n")):
        files = discover_files("**/*.py")
    assert files == ["a.py", "b.py", "c.py"]


def test_discover_files_filters_empty_lines() -> None:
    with patch("subprocess.run", return_value=_mock_run("a.py\n\nb.py\n\n")):
        files = discover_files()
    assert "" not in files
    assert files == ["a.py", "b.py"]


def test_discover_files_empty_output() -> None:
    with patch("subprocess.run", return_value=_mock_run("")):
        files = discover_files()
    assert files == []


def test_discover_files_whitespace_only_output() -> None:
    with patch("subprocess.run", return_value=_mock_run("   \n  \n")):
        files = discover_files()
    assert files == []


def test_discover_files_passes_pattern_to_git() -> None:
    with patch("subprocess.run", return_value=_mock_run("")) as mock_run:
        discover_files("*.ts")
    call_args = mock_run.call_args
    cmd = call_args[0][0]
    assert "*.ts" in cmd


def test_discover_files_uses_default_pattern() -> None:
    with patch("subprocess.run", return_value=_mock_run("")) as mock_run:
        discover_files()
    cmd = mock_run.call_args[0][0]
    assert "**/*.py" in cmd


def test_discover_files_calls_git_ls_files() -> None:
    with patch("subprocess.run", return_value=_mock_run("")) as mock_run:
        discover_files()
    cmd = mock_run.call_args[0][0]
    assert "git" in cmd
    assert "ls-files" in cmd


def test_discover_files_passes_timeout_to_subprocess() -> None:
    with patch("subprocess.run", return_value=_mock_run("")) as mock_run:
        discover_files()
    kwargs = mock_run.call_args[1]
    assert "timeout" in kwargs
    assert kwargs["timeout"] == 30


def test_discover_files_raises_on_git_failure() -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(
            128, "git", stderr="fatal: not a git repository"
        ),
    ), pytest.raises(subprocess.CalledProcessError):
        discover_files()


def test_discover_files_raises_on_timeout() -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired("git", 30),
    ), pytest.raises(subprocess.TimeoutExpired):
        discover_files()


def test_discover_files_has_docstring() -> None:
    assert discover_files.__doc__ is not None
    assert "sorted" in discover_files.__doc__.lower()


def test_batch_has_docstring() -> None:
    assert batch.__doc__ is not None
