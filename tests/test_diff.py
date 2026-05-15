"""Tests for codemonkeys.core.diff — snapshot, generate_patch, print_patch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codemonkeys.core.diff import generate_patch, print_patch, snapshot


# ---------------------------------------------------------------------------
# snapshot()
# ---------------------------------------------------------------------------


def test_snapshot_returns_ref_when_stash_create_has_output() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "abc123def456\n"

    with patch("codemonkeys.core.diff.subprocess.run", return_value=mock_result) as mock_run:
        ref = snapshot()

    mock_run.assert_called_once_with(
        ["git", "stash", "create"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert ref == "abc123def456"


def test_snapshot_returns_HEAD_when_stash_create_is_empty() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "\n"  # empty after strip

    with patch("codemonkeys.core.diff.subprocess.run", return_value=mock_result):
        ref = snapshot()

    assert ref == "HEAD"


def test_snapshot_returns_HEAD_when_stdout_is_blank() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "   "

    with patch("codemonkeys.core.diff.subprocess.run", return_value=mock_result):
        ref = snapshot()

    assert ref == "HEAD"


# ---------------------------------------------------------------------------
# generate_patch()
# ---------------------------------------------------------------------------


def test_generate_patch_returns_none_when_nothing_changed(tmp_path: Path) -> None:
    patch_path = tmp_path / "out" / "changes.patch"

    tracked_result = MagicMock()
    tracked_result.stdout = "   \n"  # only whitespace

    with patch("codemonkeys.core.diff.subprocess.run", return_value=tracked_result):
        result = generate_patch("HEAD", [], patch_path)

    assert result is None
    assert not patch_path.exists()


def test_generate_patch_writes_tracked_diff_and_returns_path(tmp_path: Path) -> None:
    patch_path = tmp_path / "out" / "changes.patch"
    tracked_diff = "diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new\n"

    tracked_result = MagicMock()
    tracked_result.stdout = tracked_diff

    with patch("codemonkeys.core.diff.subprocess.run", return_value=tracked_result):
        result = generate_patch("HEAD", [], patch_path)

    assert result == patch_path
    assert patch_path.exists()
    assert tracked_diff in patch_path.read_text()


def test_generate_patch_skips_new_file_that_does_not_exist(tmp_path: Path) -> None:
    patch_path = tmp_path / "changes.patch"
    tracked_result = MagicMock()
    tracked_result.stdout = "diff --git a/existing.py b/existing.py\n+added\n"

    with patch("codemonkeys.core.diff.subprocess.run", return_value=tracked_result):
        result = generate_patch("HEAD", ["/nonexistent/ghost_file.py"], patch_path)

    # The file doesn't exist, so it's skipped; tracked diff still written
    assert result == patch_path


def test_generate_patch_includes_diff_for_new_existing_file(tmp_path: Path) -> None:
    new_file = tmp_path / "brand_new.py"
    new_file.write_text("print('hello')\n")
    patch_path = tmp_path / "out" / "changes.patch"

    tracked_result = MagicMock()
    tracked_result.stdout = ""  # no tracked changes

    new_file_diff = "diff --git /dev/null b/brand_new.py\n+print('hello')\n"
    new_file_result = MagicMock()
    new_file_result.stdout = new_file_diff

    run_results = [tracked_result, new_file_result]

    with patch("codemonkeys.core.diff.subprocess.run", side_effect=run_results):
        result = generate_patch("HEAD", [str(new_file)], patch_path)

    assert result == patch_path
    content = patch_path.read_text()
    assert new_file_diff in content


def test_generate_patch_ignores_new_file_with_empty_diff_output(tmp_path: Path) -> None:
    new_file = tmp_path / "empty_diff.py"
    new_file.write_text("")
    patch_path = tmp_path / "changes.patch"

    tracked_result = MagicMock()
    tracked_result.stdout = ""

    empty_diff_result = MagicMock()
    empty_diff_result.stdout = "   "  # only whitespace → no addition

    with patch("codemonkeys.core.diff.subprocess.run", side_effect=[tracked_result, empty_diff_result]):
        result = generate_patch("HEAD", [str(new_file)], patch_path)

    # combined is blank → None
    assert result is None


def test_generate_patch_creates_parent_directories(tmp_path: Path) -> None:
    deep_patch_path = tmp_path / "a" / "b" / "c" / "changes.patch"
    tracked_result = MagicMock()
    tracked_result.stdout = "diff --git a/x.py b/x.py\n+x\n"

    with patch("codemonkeys.core.diff.subprocess.run", return_value=tracked_result):
        result = generate_patch("HEAD", [], deep_patch_path)

    assert result == deep_patch_path
    assert deep_patch_path.exists()


def test_generate_patch_combines_tracked_and_new_diffs(tmp_path: Path) -> None:
    new_file = tmp_path / "new.py"
    new_file.write_text("x = 1\n")
    patch_path = tmp_path / "combined.patch"

    tracked_diff = "diff --git a/old.py b/old.py\n-old\n+new\n"
    tracked_result = MagicMock()
    tracked_result.stdout = tracked_diff

    new_diff = "diff --git /dev/null b/new.py\n+x = 1\n"
    new_result = MagicMock()
    new_result.stdout = new_diff

    with patch("codemonkeys.core.diff.subprocess.run", side_effect=[tracked_result, new_result]):
        result = generate_patch("HEAD", [str(new_file)], patch_path)

    assert result == patch_path
    content = patch_path.read_text()
    assert tracked_diff in content
    assert new_diff in content


# ---------------------------------------------------------------------------
# print_patch()
# ---------------------------------------------------------------------------


def test_print_patch_reads_and_prints_content(tmp_path: Path) -> None:
    patch_file = tmp_path / "sample.patch"
    patch_file.write_text("diff --git a/foo.py b/foo.py\n+new line\n")

    mock_console = MagicMock()
    print_patch(patch_file, console=mock_console)

    # print, rule, print (Syntax), print (footer) — four console calls total
    assert mock_console.print.call_count == 3
    mock_console.rule.assert_called_once_with("Changes", style="dim")


def test_print_patch_uses_diff_syntax_highlighting(tmp_path: Path) -> None:
    patch_file = tmp_path / "hl.patch"
    patch_file.write_text("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n")

    from rich.syntax import Syntax

    captured_args: list[object] = []

    def capture(*args: object, **kwargs: object) -> None:
        captured_args.extend(args)

    mock_console = MagicMock()
    mock_console.print.side_effect = capture
    print_patch(patch_file, console=mock_console)

    syntax_instances = [a for a in captured_args if isinstance(a, Syntax)]
    assert len(syntax_instances) == 1


def test_print_patch_includes_path_in_footer(tmp_path: Path) -> None:
    patch_file = tmp_path / "footer.patch"
    patch_file.write_text("+something\n")

    printed_strings: list[str] = []

    def capture(*args: object, **kwargs: object) -> None:
        for a in args:
            if isinstance(a, str):
                printed_strings.append(a)

    mock_console = MagicMock()
    mock_console.print.side_effect = capture
    print_patch(patch_file, console=mock_console)

    assert any(str(patch_file) in s for s in printed_strings)
