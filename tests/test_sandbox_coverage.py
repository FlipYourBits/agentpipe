"""Additional tests targeting uncovered branches in codemonkeys/core/sandbox.py.

Covers:
  - restrict() dispatch to _restrict_darwin and _restrict_windows
  - _restrict_darwin() full body (home, cache_dir, profile format, env var, execvp)
  - _restrict_windows() full body (subprocess, dirs, optional dirs, env var, reexec)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import codemonkeys.core.sandbox as sandbox_module


# ---------------------------------------------------------------------------
# restrict — darwin platform dispatch
# ---------------------------------------------------------------------------


def test_restrict_dispatches_to_darwin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    with patch("codemonkeys.core.sandbox.sys") as mock_sys, \
         patch("codemonkeys.core.sandbox._restrict_darwin") as mock_darwin:
        mock_sys.platform = "darwin"
        sandbox_module.restrict(str(tmp_path))
    mock_darwin.assert_called_once()
    assert sandbox_module._RESTRICTED is True


# ---------------------------------------------------------------------------
# restrict — windows platform dispatch
# ---------------------------------------------------------------------------


def test_restrict_dispatches_to_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sandbox_module, "_RESTRICTED", False)
    with patch("codemonkeys.core.sandbox.sys") as mock_sys, \
         patch("codemonkeys.core.sandbox._restrict_windows") as mock_windows:
        mock_sys.platform = "win32"
        sandbox_module.restrict(str(tmp_path))
    mock_windows.assert_called_once()
    assert sandbox_module._RESTRICTED is True


# ---------------------------------------------------------------------------
# _restrict_darwin — full execution body (env var absent)
# ---------------------------------------------------------------------------


def test_restrict_darwin_calls_execvp(tmp_path: Path) -> None:
    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        with patch("codemonkeys.core.sandbox.os.execvp") as mock_execvp:
            sandbox_module._restrict_darwin(tmp_path)
    mock_execvp.assert_called_once()
    cmd, args = mock_execvp.call_args[0]
    assert cmd == "sandbox-exec"
    assert args[0] == "sandbox-exec"
    assert "-p" in args
    assert "--" in args


def test_restrict_darwin_profile_includes_project_dir(tmp_path: Path) -> None:
    """Profile passed to sandbox-exec must reference the allowed project directory."""
    captured: list[list[str]] = []

    def fake_execvp(cmd: str, args: list[str]) -> None:
        captured.append(list(args))

    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        with patch("codemonkeys.core.sandbox.os.execvp", side_effect=fake_execvp):
            sandbox_module._restrict_darwin(tmp_path)

    assert captured, "os.execvp was not called"
    # args: ["sandbox-exec", "-p", <profile>, "--", executable, *argv]
    profile_text = captured[0][2]
    assert str(tmp_path.resolve()) in profile_text


def test_restrict_darwin_sets_env_var_before_execvp(tmp_path: Path) -> None:
    """CODEMONKEYS_SANDBOXED must be set before execvp so re-exec skips setup."""
    env_value_at_exec: list[str] = []

    def fake_execvp(cmd: str, args: list[str]) -> None:
        env_value_at_exec.append(os.environ.get("CODEMONKEYS_SANDBOXED", ""))

    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        with patch("codemonkeys.core.sandbox.os.execvp", side_effect=fake_execvp):
            sandbox_module._restrict_darwin(tmp_path)

    assert env_value_at_exec == ["1"]


# ---------------------------------------------------------------------------
# _restrict_windows — full execution body (env var absent)
# ---------------------------------------------------------------------------


def test_restrict_windows_basic_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Main path when optional claude_data / cache dirs do not exist."""
    mock_reexec = MagicMock()
    monkeypatch.setattr(
        sandbox_module, "_reexec_low_integrity", mock_reexec, raising=False
    )

    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        env.pop("LOCALAPPDATA", None)
        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.home", return_value=tmp_path):
            sandbox_module._restrict_windows(tmp_path)

    # project dir (tmp_path) is real → icacls called at least once
    assert mock_run.called
    mock_reexec.assert_called_once()


def test_restrict_windows_sets_sandbox_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mock_reexec = MagicMock()
    monkeypatch.setattr(
        sandbox_module, "_reexec_low_integrity", mock_reexec, raising=False
    )

    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        env.pop("LOCALAPPDATA", None)
        with patch("subprocess.run"), \
             patch("pathlib.Path.home", return_value=tmp_path):
            sandbox_module._restrict_windows(tmp_path)
        # Assert inside the patch.dict context so the env hasn't been restored yet
        assert os.environ.get("CODEMONKEYS_SANDBOXED") == "1"


def test_restrict_windows_appends_optional_dirs_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """True branches for claude_data.is_dir() and cache_dir.is_dir()."""
    # Create the optional directories under the simulated home (tmp_path)
    claude_data = tmp_path / "AppData" / "Local" / "claude"
    claude_data.mkdir(parents=True)
    uv_cache = tmp_path / "AppData" / "Local" / "uv"
    uv_cache.mkdir(parents=True)

    mock_reexec = MagicMock()
    monkeypatch.setattr(
        sandbox_module, "_reexec_low_integrity", mock_reexec, raising=False
    )

    icacls_targets: list[str] = []

    def capture_run(cmd: list[str], **kwargs: object) -> None:
        icacls_targets.append(cmd[1])

    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("CODEMONKEYS_SANDBOXED", None)
        env.pop("LOCALAPPDATA", None)  # force fallback so uv path resolves under tmp_path
        with patch("subprocess.run", side_effect=capture_run), \
             patch("pathlib.Path.home", return_value=tmp_path):
            sandbox_module._restrict_windows(tmp_path)

    assert any("claude" in t for t in icacls_targets), icacls_targets
    assert any("uv" in t for t in icacls_targets), icacls_targets
    mock_reexec.assert_called_once()
