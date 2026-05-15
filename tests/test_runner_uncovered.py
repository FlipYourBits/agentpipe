"""Tests targeting the uncovered lines in codemonkeys/core/runner.py.

Covers:
- Line 122  : _on_deny callback → ToolDenied event
- Line 138  : _on_check callback → CheckResult event
- Lines 297-298: json.JSONDecodeError when structured_output is an invalid JSON string
- Lines 335-336: exception during log-save is silently swallowed
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import BaseModel

from claude_agent_sdk import ResultMessage

from codemonkeys.core.events import (
    CheckResult,
    Event,
    ToolDenied,
)
from codemonkeys.core.runner import run_agent
from codemonkeys.core.types import AgentDefinition


# ---------------------------------------------------------------------------
# Shared helpers (mirrors test_runner.py helpers without duplication of tests)
# ---------------------------------------------------------------------------


class _SimpleOutput(BaseModel):
    value: str


def _agent(**overrides) -> AgentDefinition:
    defaults = {
        "name": "cov-agent",
        "model": "sonnet",
        "system_prompt": "You are a coverage agent.",
        "tools": ["Read"],
    }
    defaults.update(overrides)
    return AgentDefinition(**defaults)


def _result_msg(
    text: str = "",
    structured_output=None,
    cost: float = 0.01,
    is_error: bool = False,
) -> ResultMessage:
    return ResultMessage(
        subtype="result",
        duration_ms=100,
        duration_api_ms=100,
        is_error=is_error,
        num_turns=1,
        session_id="cov-session",
        total_cost_usd=cost,
        usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        result=text,
        structured_output=structured_output,
        stop_reason="end_turn",
    )


# ---------------------------------------------------------------------------
# Lines 297-298: json.JSONDecodeError → raw = None → output stays None
# ---------------------------------------------------------------------------


async def _query_invalid_json(**kwargs):
    yield _result_msg(structured_output="this is {{{ not json", cost=0.01)


@pytest.mark.asyncio
async def test_structured_output_invalid_json_string_yields_none_output() -> None:
    """Lines 297-298: a non-parseable JSON string triggers JSONDecodeError; output is None."""
    with patch("codemonkeys.core.runner.query", side_effect=_query_invalid_json):
        result = await run_agent(_agent(output_schema=_SimpleOutput), "go")

    assert result.output is None
    assert result.error is None


# ---------------------------------------------------------------------------
# Lines 335-336: exception during log-save is silently swallowed
# ---------------------------------------------------------------------------


async def _query_simple(**kwargs):
    yield _result_msg(text="ok")


@pytest.mark.asyncio
async def test_save_failure_is_swallowed_result_still_returned() -> None:
    """Lines 335-336: OSError from make_log_dir is caught; run_agent still returns."""
    with (
        patch("codemonkeys.core.runner.query", side_effect=_query_simple),
        patch("codemonkeys.core.runner.make_log_dir", side_effect=OSError("no space")),
    ):
        result = await run_agent(_agent(), "go")

    assert result.error is None
    assert result.text == "ok"


# ---------------------------------------------------------------------------
# Line 122: _on_deny callback emits ToolDenied via _combined_emit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_deny_callback_emits_tool_denied_event() -> None:
    """Line 122: calling _on_deny (captured from build_permission_hooks) fires ToolDenied."""
    events: list[Event] = []
    captured_deny: list = []

    def _mock_permission_hooks(allowed_tools, on_deny=None, deny_hint=None):
        # Capture the closure; return empty dict so query runs normally
        captured_deny.append(on_deny)
        return {}

    async def _query_invokes_deny(**kwargs):
        # Fire the deny callback while run_agent is alive so _combined_emit fires
        if captured_deny and captured_deny[0] is not None:
            captured_deny[0]("Bash", "rm -rf /")
        yield _result_msg(text="done")

    with (
        patch(
            "codemonkeys.core.runner.build_permission_hooks",
            side_effect=_mock_permission_hooks,
        ),
        patch("codemonkeys.core.runner.query", side_effect=_query_invokes_deny),
    ):
        result = await run_agent(_agent(), "prompt", on_event=events.append)

    assert result.error is None
    denied = [e for e in events if isinstance(e, ToolDenied)]
    assert len(denied) == 1
    assert denied[0].tool_name == "Bash"
    assert denied[0].command == "rm -rf /"


# ---------------------------------------------------------------------------
# Line 138: _on_check callback emits CheckResult via _combined_emit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_check_callback_emits_check_result_event() -> None:
    """Line 138: calling _on_check (captured from build_check_hooks) fires CheckResult."""
    events: list[Event] = []
    captured_check: list = []

    def _mock_check_hooks(checks, agent_name="", on_check=None, **kwargs):
        # Capture the closure; return empty dict so query runs normally
        captured_check.append(on_check)
        return {}

    async def _query_invokes_check(**kwargs):
        # Fire the check callback while run_agent is alive
        if captured_check and captured_check[0] is not None:
            captured_check[0]("PostToolUse", "pytest tests/", True, "1 passed")
        yield _result_msg(text="done")

    # hooks must be non-empty so the runner calls build_check_hooks
    agent = _agent(hooks={"PostToolUse": [("*", "pytest tests/")]})

    with (
        patch(
            "codemonkeys.core.runner.build_check_hooks",
            side_effect=_mock_check_hooks,
        ),
        patch("codemonkeys.core.runner.query", side_effect=_query_invokes_check),
    ):
        result = await run_agent(agent, "prompt", on_event=events.append)

    assert result.error is None
    checks = [e for e in events if isinstance(e, CheckResult)]
    assert len(checks) == 1
    assert checks[0].hook_event == "PostToolUse"
    assert checks[0].command == "pytest tests/"
    assert checks[0].passed is True
