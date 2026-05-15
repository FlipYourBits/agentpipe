"""Characterization tests for codemonkeys/core/_sandbox_win32.py.

ctypes.windll is Windows-only, but since it is only accessed inside
_reexec_low_integrity (not at import time), we can exercise the function on any
platform by patching ctypes.windll with a MagicMock.
"""

from __future__ import annotations

import ctypes
from unittest.mock import MagicMock, call, patch

import pytest

# Guard the entire module import so the test file can still be collected on
# platforms where ctypes.wintypes is incomplete.
try:
    import codemonkeys.core._sandbox_win32 as win32_mod

    _IMPORTABLE = True
except (ImportError, AttributeError, OSError):
    _IMPORTABLE = False

pytestmark = pytest.mark.skipif(
    not _IMPORTABLE,
    reason="ctypes.wintypes not fully available on this platform",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_windll(
    *,
    open_process_token: int = 1,
    duplicate_token: int = 1,
    set_token_info: int = 1,
    create_process: int = 1,
) -> MagicMock:
    """Return a fake ctypes.windll whose kernel32/advapi32 honour the given return values."""
    kernel32 = MagicMock()
    kernel32.GetCurrentProcess.return_value = 1
    kernel32.OpenProcessToken.return_value = open_process_token
    kernel32.WaitForSingleObject.return_value = 0
    kernel32.GetExitCodeProcess.return_value = 1
    kernel32.CloseHandle.return_value = 1

    advapi32 = MagicMock()
    advapi32.DuplicateTokenEx.return_value = duplicate_token
    advapi32.SetTokenInformation.return_value = set_token_info
    advapi32.CreateProcessWithTokenW.return_value = create_process

    windll = MagicMock()
    windll.kernel32 = kernel32
    windll.advapi32 = advapi32
    return windll


# ---------------------------------------------------------------------------
# _reexec_low_integrity — failure paths (OSError branches)
# ---------------------------------------------------------------------------


def test_reexec_low_integrity_open_process_token_failure() -> None:
    """OpenProcessToken returning 0 must raise OSError with the right message."""
    windll = _make_windll(open_process_token=0)
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError, match="OpenProcessToken failed"):
            win32_mod._reexec_low_integrity()


def test_reexec_low_integrity_duplicate_token_failure() -> None:
    """DuplicateTokenEx returning 0 must raise OSError with the right message."""
    windll = _make_windll(duplicate_token=0)
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError, match="DuplicateTokenEx failed"):
            win32_mod._reexec_low_integrity()


def test_reexec_low_integrity_set_token_information_failure() -> None:
    """SetTokenInformation returning 0 must raise OSError with the right message."""
    windll = _make_windll(set_token_info=0)
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError, match="SetTokenInformation failed"):
            win32_mod._reexec_low_integrity()


def test_reexec_low_integrity_create_process_failure() -> None:
    """CreateProcessWithTokenW returning 0 must raise OSError with the right message."""
    windll = _make_windll(create_process=0)
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError, match="CreateProcessWithTokenW failed"):
            win32_mod._reexec_low_integrity()


# ---------------------------------------------------------------------------
# _reexec_low_integrity — success path (post-spawn lines)
# ---------------------------------------------------------------------------


def test_reexec_low_integrity_success_calls_sys_exit() -> None:
    """When all Win32 calls succeed, the function exits with the child's exit code."""
    windll = _make_windll()
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(SystemExit) as exc_info:
            win32_mod._reexec_low_integrity()

    # GetExitCodeProcess doesn't write through the mock so exit_code stays 0.
    assert exc_info.value.code == 0


def test_reexec_low_integrity_success_waits_for_process() -> None:
    """WaitForSingleObject must be called with INFINITE (0xFFFFFFFF) timeout."""
    windll = _make_windll()
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(SystemExit):
            win32_mod._reexec_low_integrity()

    kernel32 = windll.kernel32
    assert kernel32.WaitForSingleObject.called
    _, timeout = kernel32.WaitForSingleObject.call_args[0]
    assert timeout == 0xFFFFFFFF


def test_reexec_low_integrity_success_closes_all_handles() -> None:
    """CloseHandle must be called four times: hProcess, hThread, h_token, h_new."""
    windll = _make_windll()
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(SystemExit):
            win32_mod._reexec_low_integrity()

    assert windll.kernel32.CloseHandle.call_count == 4


def test_reexec_low_integrity_success_queries_exit_code() -> None:
    """GetExitCodeProcess must be called once after WaitForSingleObject."""
    windll = _make_windll()
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(SystemExit):
            win32_mod._reexec_low_integrity()

    assert windll.kernel32.GetExitCodeProcess.call_count == 1


# ---------------------------------------------------------------------------
# Constants — spot-check values that flow into Win32 calls
# ---------------------------------------------------------------------------


def test_reexec_low_integrity_passes_correct_access_mask_to_open_process_token() -> None:
    """OpenProcessToken access mask must be TOKEN_DUPLICATE|QUERY|ADJUST|ASSIGN."""
    expected = 0x0002 | 0x0008 | 0x0080 | 0x0001  # = 0x8B
    windll = _make_windll(open_process_token=0)  # fail early to inspect the call
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError):
            win32_mod._reexec_low_integrity()

    _, access_mask, _ = windll.kernel32.OpenProcessToken.call_args[0]
    assert access_mask == expected


def test_reexec_low_integrity_passes_logon_with_profile_to_create_process() -> None:
    """CreateProcessWithTokenW logon flags must be LOGON_WITH_PROFILE (0x1)."""
    windll = _make_windll(create_process=0)  # fail after reaching CreateProcess
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError):
            win32_mod._reexec_low_integrity()

    _, logon_flags, *_ = windll.advapi32.CreateProcessWithTokenW.call_args[0]
    assert logon_flags == 0x00000001


def test_reexec_low_integrity_passes_integrity_level_to_set_token_info() -> None:
    """SetTokenInformation info class must be TokenIntegrityLevel (25)."""
    windll = _make_windll(set_token_info=0)  # fail after reaching SetTokenInformation
    with patch("ctypes.windll", windll, create=True):
        with pytest.raises(OSError):
            win32_mod._reexec_low_integrity()

    _, info_class, _, _ = windll.advapi32.SetTokenInformation.call_args[0]
    assert info_class == 25
