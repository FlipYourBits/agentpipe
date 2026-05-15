"""Characterization tests for codemonkeys/core/sandbox.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import codemonkeys.core.sandbox as sandbox_module


# ---------------------------------------------------------------------------
# is_restricted
# ---------------------------------------------------------------------------


def test_is_restricted_returns_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    assert sandbox_module.is_restricted() is False


def test_is_restricted_reflects_true_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", True)
    assert sandbox_module.is_restricted() is True


# ---------------------------------------------------------------------------
# restrict — guard conditions
# ---------------------------------------------------------------------------


def test_restrict_is_noop_when_already_restricted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", True)
    # Should return immediately without error or state change
    sandbox_module.restrict(str(tmp_path))
    assert sandbox_module._RESTRICTED is True


def test_restrict_raises_for_nonexistent_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    with pytest.raises(ValueError, match="not a directory"):
        sandbox_module.restrict("/nonexistent/path/abc123")


def test_restrict_raises_for_file_not_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    f = tmp_path / "regular_file.txt"
    f.write_text("content")
    with pytest.raises(ValueError, match="not a directory"):
        sandbox_module.restrict(str(f))


# ---------------------------------------------------------------------------
# restrict — linux platform path (the actual running platform in CI)
# ---------------------------------------------------------------------------


def test_restrict_linux_sets_restricted_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    with patch("codemonkeys.core.sandbox._restrict_linux"):
        if sys.platform == "linux":
            sandbox_module.restrict(str(tmp_path))
        else:
            pytest.skip("linux-only branch")
    assert sandbox_module._RESTRICTED is True


def test_restrict_accepts_path_object(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    with patch("codemonkeys.core.sandbox._restrict_linux"):
        if sys.platform == "linux":
            sandbox_module.restrict(tmp_path)  # Path object, not str
        else:
            pytest.skip("linux-only branch")
    assert sandbox_module._RESTRICTED is True


# ---------------------------------------------------------------------------
# restrict — unsupported platform path
# ---------------------------------------------------------------------------


def test_restrict_unsupported_platform_logs_warning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    # Simulate an unsupported platform — restrict returns without setting flag
    with patch("codemonkeys.core.sandbox.sys") as mock_sys:
        mock_sys.platform = "freebsd14"
        sandbox_module.restrict(str(tmp_path))
    # On unsupported platforms, _RESTRICTED is NOT set (function returns early)
    assert sandbox_module._RESTRICTED is False


# ---------------------------------------------------------------------------
# _restrict_darwin — early return when env var is set
# ---------------------------------------------------------------------------


def test_restrict_darwin_returns_early_if_sandboxed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CODEMONKEYS_SANDBOXED", "1")
    # _restrict_darwin should return without calling execvp
    sandbox_module._restrict_darwin(tmp_path)  # no exception → early return worked


# ---------------------------------------------------------------------------
# _restrict_windows — early return when env var is set
# ---------------------------------------------------------------------------


def test_restrict_windows_returns_early_if_sandboxed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CODEMONKEYS_SANDBOXED", "1")
    # _restrict_windows should return without calling icacls or re-exec
    sandbox_module._restrict_windows(tmp_path)  # no exception → early return worked


# ---------------------------------------------------------------------------
# _restrict_linux — landlock import failure path
# ---------------------------------------------------------------------------


def test_restrict_linux_without_landlock_is_noop(tmp_path: Path) -> None:
    # Simulate ImportError from landlock
    with patch.dict("sys.modules", {"landlock": None}):
        # Should log a warning and return without raising
        sandbox_module._restrict_linux(tmp_path)


# ---------------------------------------------------------------------------
# _sandbox_win32 — structure definitions (importable on all platforms)
# ---------------------------------------------------------------------------


def test_sandbox_win32_structures_importable() -> None:
    try:
        from codemonkeys.core._sandbox_win32 import (
            PROCESS_INFORMATION,
            SID_AND_ATTRIBUTES,
            STARTUPINFOW,
            TOKEN_MANDATORY_LABEL,
        )

        # Check that each structure has _fields_
        assert hasattr(SID_AND_ATTRIBUTES, "_fields_")
        assert hasattr(TOKEN_MANDATORY_LABEL, "_fields_")
        assert hasattr(STARTUPINFOW, "_fields_")
        assert hasattr(PROCESS_INFORMATION, "_fields_")
    except (ImportError, AttributeError, OSError):
        pytest.skip("ctypes.wintypes not fully available on this platform")


def test_sandbox_win32_sid_and_attributes_fields() -> None:
    try:
        from codemonkeys.core._sandbox_win32 import SID_AND_ATTRIBUTES

        field_names = [f[0] for f in SID_AND_ATTRIBUTES._fields_]
        assert "Sid" in field_names
        assert "Attributes" in field_names
    except (ImportError, AttributeError, OSError):
        pytest.skip("ctypes.wintypes not fully available on this platform")


def test_sandbox_win32_process_information_fields() -> None:
    try:
        from codemonkeys.core._sandbox_win32 import PROCESS_INFORMATION

        field_names = [f[0] for f in PROCESS_INFORMATION._fields_]
        assert "hProcess" in field_names
        assert "hThread" in field_names
        assert "dwProcessId" in field_names
        assert "dwThreadId" in field_names
    except (ImportError, AttributeError, OSError):
        pytest.skip("ctypes.wintypes not fully available on this platform")


def test_sandbox_win32_startupinfow_has_cb_field() -> None:
    try:
        from codemonkeys.core._sandbox_win32 import STARTUPINFOW

        field_names = [f[0] for f in STARTUPINFOW._fields_]
        assert "cb" in field_names
        assert "hStdInput" in field_names
        assert "hStdOutput" in field_names
        assert "hStdError" in field_names
    except (ImportError, AttributeError, OSError):
        pytest.skip("ctypes.wintypes not fully available on this platform")
