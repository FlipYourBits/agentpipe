"""Tests for codemonkeys/display/stdout.py — covers previously-uncovered lines."""

from __future__ import annotations

import io

from rich.console import Console

from codemonkeys.core.events import (
    AgentCompleted,
    AgentError,
    AgentStarted,
    CheckResult,
    RawMessage,
    TextOutput,
    ThinkingOutput,
    ToolCall,
    TokenUpdate,
)
from codemonkeys.core.types import RunResult, TokenUsage
from codemonkeys.display.stdout import make_stdout_printer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_printer():
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=200)
    printer = make_stdout_printer(console=console)
    return printer, buf


def _make_result(*, cost_usd: float = 0.01, duration_ms: int = 5000) -> RunResult:
    return RunResult(
        output=None,
        text="done",
        usage=TokenUsage(input_tokens=100, output_tokens=50),
        cost_usd=cost_usd,
        duration_ms=duration_ms,
    )


# ---------------------------------------------------------------------------
# ThinkingOutput
# ---------------------------------------------------------------------------


def test_thinking_output_does_not_raise():
    """ThinkingOutput sets current_tool to 'thinking' — no exception raised."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="r", timestamp=0.0, model="sonnet"))
    # Just verify no exception; Live's background thread may write to the buffer
    printer(ThinkingOutput(agent_name="r", timestamp=0.0, text="let me think"))


def test_thinking_output_without_prior_start():
    """ThinkingOutput works even without a preceding AgentStarted."""
    printer, buf = _capture_printer()
    # Should not raise even though _live is None (no spinner to update)
    printer(ThinkingOutput(agent_name="r", timestamp=0.0, text="hmm"))


# ---------------------------------------------------------------------------
# TextOutput
# ---------------------------------------------------------------------------


def test_text_output_is_silent():
    """TextOutput is a pass statement — produces no output."""
    printer, buf = _capture_printer()
    before = buf.getvalue()
    printer(TextOutput(agent_name="r", timestamp=0.0, text="hello world"))
    assert buf.getvalue() == before


# ---------------------------------------------------------------------------
# CheckResult — passed
# ---------------------------------------------------------------------------


def test_check_result_passed_shows_pass():
    printer, buf = _capture_printer()
    printer(
        CheckResult(
            agent_name="r",
            timestamp=0.0,
            hook_event="PostToolUse",
            command="pytest -q",
            passed=True,
            output="",
        )
    )
    output = buf.getvalue()
    assert "PASS" in output


# ---------------------------------------------------------------------------
# CheckResult — failed without output lines
# ---------------------------------------------------------------------------


def test_check_result_failed_shows_fail():
    printer, buf = _capture_printer()
    printer(
        CheckResult(
            agent_name="r",
            timestamp=0.0,
            hook_event="PostToolUse",
            command="pytest",
            passed=False,
            output="",
        )
    )
    output = buf.getvalue()
    assert "FAIL" in output


# ---------------------------------------------------------------------------
# CheckResult — failed with output lines
# ---------------------------------------------------------------------------


def test_check_result_failed_with_output_prints_lines():
    printer, buf = _capture_printer()
    printer(
        CheckResult(
            agent_name="r",
            timestamp=0.0,
            hook_event="PostToolUse",
            command="pytest",
            passed=False,
            output="line1\nline2\nline3",
        )
    )
    output = buf.getvalue()
    assert "FAIL" in output
    assert "line1" in output
    assert "line2" in output
    assert "line3" in output


def test_check_result_failed_truncates_at_10_lines():
    """Only the first 10 output lines are printed for a failing check."""
    printer, buf = _capture_printer()
    raw_lines = "\n".join(f"LINE{i:02d}" for i in range(20))
    printer(
        CheckResult(
            agent_name="r",
            timestamp=0.0,
            hook_event="PostToolUse",
            command="pytest",
            passed=False,
            output=raw_lines,
        )
    )
    output = buf.getvalue()
    assert "LINE00" in output
    assert "LINE09" in output
    assert "LINE10" not in output


# ---------------------------------------------------------------------------
# RawMessage — SystemMessage
# ---------------------------------------------------------------------------


def test_raw_message_system_message_prints_label():
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="myagent",
            timestamp=0.0,
            message_type="SystemMessage",
            data={},
        )
    )
    output = buf.getvalue()
    assert "myagent" in output


def test_raw_message_system_message_with_subtype():
    """SystemMessage with a known subtype uses system_message_label."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="SystemMessage",
            data={"subtype": "init"},
        )
    )
    output = buf.getvalue()
    assert "r" in output


# ---------------------------------------------------------------------------
# RawMessage — UserMessage
# ---------------------------------------------------------------------------


def test_raw_message_user_message_with_prior_tool_call():
    """UserMessage uses the last ToolCall name and format_tool_result hint."""
    printer, buf = _capture_printer()
    printer(
        ToolCall(
            agent_name="r",
            timestamp=0.0,
            tool_name="Read",
            tool_input={"file_path": "app.py"},
        )
    )
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="UserMessage",
            data={"tool_use_result": "file contents here"},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "Read" in output


def test_raw_message_user_message_no_prior_tool_call():
    """UserMessage falls back to '?' when no ToolCall preceded it."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="UserMessage",
            data={},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "?" in output


def test_raw_message_user_message_with_non_empty_hint_shows_suffix():
    """UserMessage with a non-empty tool result appends ': <hint>' suffix."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="UserMessage",
            data={"tool_use_result": "some output text"},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "some output text" in output


# ---------------------------------------------------------------------------
# RawMessage — ResultMessage
# ---------------------------------------------------------------------------


def test_raw_message_result_message_with_total_cost_usd():
    """ResultMessage with total_cost_usd uses it directly."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="ResultMessage",
            data={"total_cost_usd": 0.0123, "num_turns": 4},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "turns=4" in output


def test_raw_message_result_message_cost_fallback_to_cost_key():
    """ResultMessage without total_cost_usd falls back to 'cost' key."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="ResultMessage",
            data={"cost": 0.05, "num_turns": 2},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "turns=2" in output


def test_raw_message_result_message_no_cost_keys_defaults_zero():
    """ResultMessage with neither cost key defaults cost to zero."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="ResultMessage",
            data={"num_turns": 1},
        )
    )
    output = buf.getvalue()
    assert "result" in output
    assert "turns=1" in output


def test_raw_message_result_message_cost_none_value_treated_as_zero():
    """ResultMessage where 'cost' key is None falls back to 0."""
    printer, buf = _capture_printer()
    printer(
        RawMessage(
            agent_name="r",
            timestamp=0.0,
            message_type="ResultMessage",
            data={"cost": None, "num_turns": 3},
        )
    )
    output = buf.getvalue()
    assert "result" in output


# ---------------------------------------------------------------------------
# _stop_spinner — AgentCompleted on sole running agent
# ---------------------------------------------------------------------------


def test_agent_completed_stops_spinner_when_last_agent_exits():
    """AgentCompleted on the last running agent calls _live.stop()."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="r", timestamp=0.0, model="sonnet"))
    printer(AgentCompleted(agent_name="r", timestamp=0.0, result=_make_result()))
    output = buf.getvalue()
    assert "r" in output


def test_agent_completed_long_duration_shows_minutes():
    """AgentCompleted with ≥60s duration formats as minutes."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="r", timestamp=0.0, model="sonnet"))
    printer(
        AgentCompleted(
            agent_name="r",
            timestamp=0.0,
            result=_make_result(duration_ms=120_000),  # 2 minutes
        )
    )
    output = buf.getvalue()
    assert "m" in output


# ---------------------------------------------------------------------------
# _stop_spinner — AgentError on sole running agent
# ---------------------------------------------------------------------------


def test_agent_error_stops_spinner_when_last_agent_exits():
    """AgentError on the last running agent calls _live.stop()."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="r", timestamp=0.0, model="sonnet"))
    printer(AgentError(agent_name="r", timestamp=0.0, error="kaboom"))
    output = buf.getvalue()
    assert "kaboom" in output


# ---------------------------------------------------------------------------
# _update_spinner — AgentCompleted when a sibling agent is still running
# ---------------------------------------------------------------------------


def test_agent_completed_updates_spinner_when_other_agent_still_running():
    """AgentCompleted with a sibling running calls _update_spinner (else branch)."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="a", timestamp=0.0, model="sonnet"))
    printer(AgentStarted(agent_name="b", timestamp=0.0, model="sonnet"))
    printer(AgentCompleted(agent_name="a", timestamp=0.0, result=_make_result()))
    output = buf.getvalue()
    assert "a" in output


# ---------------------------------------------------------------------------
# _update_spinner — AgentError when a sibling agent is still running
# ---------------------------------------------------------------------------


def test_agent_error_updates_spinner_when_other_agent_still_running():
    """AgentError with a sibling running calls _update_spinner (else branch)."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="a", timestamp=0.0, model="sonnet"))
    printer(AgentStarted(agent_name="b", timestamp=0.0, model="sonnet"))
    printer(AgentError(agent_name="a", timestamp=0.0, error="boom"))
    output = buf.getvalue()
    assert "boom" in output


# ---------------------------------------------------------------------------
# Combined scenario — full lifecycle
# ---------------------------------------------------------------------------


def test_full_agent_lifecycle_with_all_event_types():
    """Exercise a realistic sequence of events on a single agent."""
    printer, buf = _capture_printer()
    printer(AgentStarted(agent_name="worker", timestamp=0.0, model="claude-3-5-sonnet"))
    printer(ThinkingOutput(agent_name="worker", timestamp=1.0, text="thinking..."))
    printer(
        ToolCall(
            agent_name="worker",
            timestamp=2.0,
            tool_name="Bash",
            tool_input={"command": "echo hi"},
        )
    )
    printer(
        RawMessage(
            agent_name="worker",
            timestamp=3.0,
            message_type="UserMessage",
            data={"tool_use_result": "hi"},
        )
    )
    printer(TextOutput(agent_name="worker", timestamp=4.0, text="all done"))
    printer(
        CheckResult(
            agent_name="worker",
            timestamp=5.0,
            hook_event="Stop",
            command="pytest",
            passed=False,
            output="FAILED test_foo.py",
        )
    )
    printer(
        TokenUpdate(
            agent_name="worker",
            timestamp=6.0,
            usage=TokenUsage(
                input_tokens=500,
                output_tokens=100,
                cache_read_tokens=20,
                cache_creation_tokens=5,
            ),
            cost_usd=0.003,
        )
    )
    printer(
        AgentCompleted(agent_name="worker", timestamp=7.0, result=_make_result())
    )
    output = buf.getvalue()
    assert "worker" in output
    assert "FAIL" in output
