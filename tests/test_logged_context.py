from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from codemonkeys.core.events import AgentStarted
from codemonkeys.display.logger import FileLogger, logged


def test_logged_writes_events_to_named_file() -> None:
    """logged() creates <name>_events.jsonl inside log_dir (line 41) and fans events
    through to the file logger (line 43)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        no_op = lambda event: None  # noqa: E731

        with logged(log_dir, "myrun", printer=no_op) as handler:
            handler(AgentStarted(agent_name="test", timestamp=1000.0, model="sonnet"))

        log_file = log_dir / "myrun_events.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0])["agent_name"] == "test"


def test_logged_without_printer_creates_stdout_printer() -> None:
    """When printer is None, logged() must call make_stdout_printer (lines 39-40)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        with patch("codemonkeys.display.logger.make_stdout_printer") as mock_make:
            mock_make.return_value = lambda event: None
            with logged(log_dir, "noprinter") as handler:
                handler(AgentStarted(agent_name="np", timestamp=1000.0, model="sonnet"))
            mock_make.assert_called_once()

        log_file = log_dir / "noprinter_events.jsonl"
        assert log_file.exists()


def test_logged_closes_logger_on_exit() -> None:
    """The finally block (line 45) must close the FileLogger on context-manager exit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        no_op = lambda event: None  # noqa: E731

        with patch.object(FileLogger, "close") as mock_close:
            with logged(log_dir, "closing", printer=no_op):
                pass
            mock_close.assert_called_once()
