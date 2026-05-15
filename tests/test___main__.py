from __future__ import annotations

import runpy
from unittest.mock import MagicMock, patch


def test_main_module_imports_and_calls_main() -> None:
    """Running codemonkeys as a module imports cli.main and calls it."""
    mock_main = MagicMock()
    with patch("codemonkeys.cli.main", mock_main):
        runpy.run_module("codemonkeys.__main__", run_name="__main__", alter_sys=True)

    mock_main.assert_called_once_with()
