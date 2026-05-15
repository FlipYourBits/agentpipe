"""Tests for codemonkeys/display/file_printer.py."""

from __future__ import annotations

import time
from pathlib import Path

from codemonkeys.core.events import (
    AgentCompleted,
    AgentError,
    AgentStarted,
    CheckResult,
    ThinkingOutput,
    ToolCall,
    ToolDenied,
    TokenUpdate,
)
from codemonkeys.core.types import RunResult, TokenUsage
from codemonkeys.display.file_printer import make_file_printer


def _ts() -> float:
    return time.time()


def test_creates_log_file(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(AgentStarted(agent_name="test_agent", timestamp=_ts(), model="sonnet"))
    assert log_file.exists()


def test_logs_agent_started(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(AgentStarted(agent_name="test_agent", timestamp=_ts(), model="sonnet"))
    content = log_file.read_text()
    assert "test_agent" in content
    assert "sonnet" in content


def test_logs_tool_call(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(AgentStarted(agent_name="a", timestamp=_ts(), model="sonnet"))
    printer(ToolCall(agent_name="a", timestamp=_ts(), tool_name="Read", tool_input={"file_path": "x.py"}))
    content = log_file.read_text()
    assert "Read(x.py)" in content


def test_logs_tool_denied(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(ToolDenied(agent_name="a", timestamp=_ts(), tool_name="Edit", command="Edit(secret.py)"))
    content = log_file.read_text()
    assert "DENIED" in content


def test_logs_thinking(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(ThinkingOutput(agent_name="a", timestamp=_ts(), text="analyzing the code"))
    content = log_file.read_text()
    assert "analyzing the code" in content


def test_logs_token_update(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    usage = TokenUsage(input_tokens=100, output_tokens=50, cache_read_tokens=0, cache_creation_tokens=0)
    printer(TokenUpdate(agent_name="a", timestamp=_ts(), usage=usage, cost_usd=0.0123))
    content = log_file.read_text()
    assert "$0.0123" in content


def test_logs_check_result(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(CheckResult(agent_name="a", timestamp=_ts(), hook_event="Stop", command="pytest", passed=False, output="1 failed"))
    content = log_file.read_text()
    assert "FAIL" in content
    assert "pytest" in content


def test_logs_agent_completed(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    result = RunResult(
        output=None, text="", usage=TokenUsage(input_tokens=0, output_tokens=0),
        cost_usd=0.5, duration_ms=30000, error=None,
    )
    printer(AgentCompleted(agent_name="a", timestamp=_ts(), result=result))
    content = log_file.read_text()
    assert "$0.5" in content or "$0.50" in content


def test_logs_agent_error(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(AgentError(agent_name="a", timestamp=_ts(), error="something broke"))
    content = log_file.read_text()
    assert "ERROR" in content
    assert "something broke" in content


def test_multiple_events_appended(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    printer = make_file_printer(log_file)
    printer(AgentStarted(agent_name="a", timestamp=_ts(), model="sonnet"))
    printer(ToolCall(agent_name="a", timestamp=_ts(), tool_name="Read", tool_input={"file_path": "x.py"}))
    printer(ToolCall(agent_name="a", timestamp=_ts(), tool_name="Edit", tool_input={"file_path": "x.py"}))
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) >= 3
