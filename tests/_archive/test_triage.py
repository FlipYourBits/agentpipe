"""Tests for codemonkeys/agents/triage.py and codemonkeys/orchestration.py."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from codemonkeys.agents.triage import (
    TriageResult,
    _default_formatter,
    make_triage,
)
from codemonkeys.orchestration import _prompt_user, run_triage
from codemonkeys.core.types import AgentDefinition, RunResult, TokenUsage


# ---------------------------------------------------------------------------
# _default_formatter — string input
# ---------------------------------------------------------------------------


def test_default_formatter_string() -> None:
    assert _default_formatter("hello world") == "hello world"


def test_default_formatter_empty_string() -> None:
    assert _default_formatter("") == ""


# ---------------------------------------------------------------------------
# _default_formatter — BaseModel input
# ---------------------------------------------------------------------------


class SampleModel(BaseModel):
    title: str
    severity: str
    note: str | None = None


def test_default_formatter_base_model_no_none() -> None:
    item = SampleModel(title="Bug", severity="high")
    result = _default_formatter(item)
    assert result == "title: Bug | severity: high"


def test_default_formatter_base_model_excludes_none() -> None:
    item = SampleModel(title="Bug", severity="high", note=None)
    result = _default_formatter(item)
    # none fields should be excluded
    assert "note" not in result
    assert "title: Bug" in result
    assert "severity: high" in result


def test_default_formatter_base_model_with_all_fields() -> None:
    item = SampleModel(title="Crash", severity="critical", note="details here")
    result = _default_formatter(item)
    assert "title: Crash" in result
    assert "severity: critical" in result
    assert "note: details here" in result


# ---------------------------------------------------------------------------
# _default_formatter — dict input
# ---------------------------------------------------------------------------


def test_default_formatter_dict_simple() -> None:
    item = {"key": "value", "num": 42}
    result = _default_formatter(item)
    assert "key: value" in result
    assert "num: 42" in result


def test_default_formatter_dict_skips_none_values() -> None:
    item = {"key": "value", "empty": None}
    result = _default_formatter(item)
    assert "key: value" in result
    assert "empty" not in result


def test_default_formatter_dict_all_none() -> None:
    item = {"a": None, "b": None}
    result = _default_formatter(item)
    assert result == ""


# ---------------------------------------------------------------------------
# _default_formatter — fallback (non-str, non-BaseModel, non-dict)
# ---------------------------------------------------------------------------


def test_default_formatter_int_falls_back_to_str() -> None:
    assert _default_formatter(42) == "42"


def test_default_formatter_list_falls_back_to_str() -> None:
    assert _default_formatter([1, 2, 3]) == "[1, 2, 3]"


def test_default_formatter_custom_object_falls_back_to_str() -> None:
    class Opaque:
        def __repr__(self) -> str:
            return "OpaqueObject"

    result = _default_formatter(Opaque())
    assert result == "OpaqueObject"


# ---------------------------------------------------------------------------
# make_triage — returns a valid AgentDefinition
# ---------------------------------------------------------------------------


def test_make_triage_returns_agent_definition() -> None:
    items = ["finding one", "finding two"]
    agent = make_triage(items)
    assert isinstance(agent, AgentDefinition)
    assert agent.name == "triage"
    assert agent.output_schema is TriageResult


def test_make_triage_system_prompt_contains_numbered_items() -> None:
    items = ["alpha", "beta", "gamma"]
    agent = make_triage(items)
    assert "1. alpha" in agent.system_prompt
    assert "2. beta" in agent.system_prompt
    assert "3. gamma" in agent.system_prompt


def test_make_triage_with_custom_formatter() -> None:
    items = [{"name": "X"}, {"name": "Y"}]
    formatter = lambda item: item["name"].upper()  # noqa: E731
    agent = make_triage(items, formatter=formatter)
    assert "1. X" in agent.system_prompt
    assert "2. Y" in agent.system_prompt


def test_make_triage_default_formatter_used_when_none() -> None:
    items = ["only item"]
    agent = make_triage(items, formatter=None)
    assert "1. only item" in agent.system_prompt


# ---------------------------------------------------------------------------
# run_triage — early exit on empty / 'none' input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_triage_empty_input_returns_empty() -> None:
    with patch("builtins.input", return_value=""):
        result = await run_triage(["item1", "item2"])
    assert result == []


@pytest.mark.asyncio
async def test_run_triage_none_input_returns_empty() -> None:
    with patch("builtins.input", return_value="none"):
        result = await run_triage(["item1", "item2"])
    assert result == []


@pytest.mark.asyncio
async def test_run_triage_none_uppercase_returns_empty() -> None:
    with patch("builtins.input", return_value="NONE"):
        result = await run_triage(["item1", "item2"])
    assert result == []


@pytest.mark.asyncio
async def test_run_triage_whitespace_only_returns_empty() -> None:
    with patch("builtins.input", return_value="   "):
        result = await run_triage(["item1", "item2"])
    assert result == []


# ---------------------------------------------------------------------------
# run_triage — runs agent, returns selected items
# ---------------------------------------------------------------------------


def _make_run_result(triage_result: TriageResult | None) -> RunResult:
    usage = TokenUsage(input_tokens=100, output_tokens=50)
    return RunResult(
        output=triage_result,
        text="",
        usage=usage,
        cost_usd=0.001,
        duration_ms=200,
    )


@pytest.mark.asyncio
async def test_run_triage_returns_selected_items() -> None:
    items = ["alpha", "beta", "gamma"]
    triage_result = TriageResult(selected=[1, 3], summary="first and third")
    mock_result = _make_run_result(triage_result)

    with (
        patch("builtins.input", return_value="first and third"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(items)

    assert result == ["alpha", "gamma"]


@pytest.mark.asyncio
async def test_run_triage_passes_formatter_to_make_triage() -> None:
    items = [{"name": "A"}, {"name": "B"}]
    triage_result = TriageResult(selected=[2], summary="second")
    mock_result = _make_run_result(triage_result)
    formatter = lambda item: item["name"]  # noqa: E731

    with (
        patch("builtins.input", return_value="second"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(items, formatter=formatter)

    assert result == [{"name": "B"}]


@pytest.mark.asyncio
async def test_run_triage_no_output_returns_empty() -> None:
    mock_result = _make_run_result(None)

    with (
        patch("builtins.input", return_value="all"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(["item1"])

    assert result == []


@pytest.mark.asyncio
async def test_run_triage_empty_selected_list_returns_empty() -> None:
    triage_result = TriageResult(selected=[], summary="nothing selected")
    mock_result = _make_run_result(triage_result)

    with (
        patch("builtins.input", return_value="none of them"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(["item1", "item2"])

    assert result == []


@pytest.mark.asyncio
async def test_run_triage_non_triage_result_output_returns_empty() -> None:
    """If result.output is some other BaseModel, fall back to []."""

    class OtherModel(BaseModel):
        data: str

    usage = TokenUsage(input_tokens=10, output_tokens=5)
    mock_result = RunResult(
        output=OtherModel(data="x"),
        text="",
        usage=usage,
        cost_usd=0.0,
        duration_ms=10,
    )

    with (
        patch("builtins.input", return_value="all"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(["item"])

    assert result == []


@pytest.mark.asyncio
async def test_run_triage_forwards_on_event_and_log_dir(tmp_path) -> None:
    items = ["x"]
    triage_result = TriageResult(selected=[1], summary="first")
    mock_result = _make_run_result(triage_result)
    on_event = MagicMock()

    with (
        patch("builtins.input", return_value="first"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(items, on_event=on_event, log_dir=tmp_path)

    mock_run.assert_awaited_once()
    _call_kwargs = mock_run.call_args
    assert _call_kwargs.kwargs.get("on_event") is on_event
    assert _call_kwargs.kwargs.get("log_dir") is tmp_path
    assert result == ["x"]


# ---------------------------------------------------------------------------
# _prompt_user — async wrapper around input()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prompt_user_runs_input_in_executor() -> None:
    """_prompt_user should call input() via run_in_executor, not block the loop."""
    with patch("codemonkeys.orchestration.input", return_value="  hello  "):
        result = await _prompt_user("prompt> ")
    assert result == "  hello  "


# ---------------------------------------------------------------------------
# run_triage — logs warning on unexpected output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_triage_logs_warning_on_non_triage_output(caplog) -> None:
    """When agent returns unexpected output, a warning should be logged."""

    class OtherModel(BaseModel):
        data: str

    usage = TokenUsage(input_tokens=10, output_tokens=5)
    mock_result = RunResult(
        output=OtherModel(data="x"),
        text="",
        usage=usage,
        cost_usd=0.0,
        duration_ms=10,
        error="some SDK error",
    )

    with (
        caplog.at_level(logging.WARNING, logger="codemonkeys.orchestration"),
        patch("builtins.input", return_value="all"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(["item"])

    assert result == []
    assert "unexpected output" in caplog.text
    assert "some SDK error" in caplog.text


@pytest.mark.asyncio
async def test_run_triage_logs_warning_on_none_output(caplog) -> None:
    """When agent returns None output, a warning should be logged."""
    mock_result = _make_run_result(None)

    with (
        caplog.at_level(logging.WARNING, logger="codemonkeys.orchestration"),
        patch("builtins.input", return_value="all"),
        patch(
            "codemonkeys.orchestration.run_agent", new_callable=AsyncMock
        ) as mock_run,
    ):
        mock_run.return_value = mock_result
        result = await run_triage(["item1"])

    assert result == []
    assert "unexpected output" in caplog.text


# ---------------------------------------------------------------------------
# run_triage — custom prompt parameter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_triage_custom_prompt_passed_to_input() -> None:
    """The custom prompt should be forwarded to the input call."""
    with patch("builtins.input", return_value="") as mock_input:
        await run_triage(["item1"], prompt="Pick items> ")

    mock_input.assert_called_once()
    call_arg = mock_input.call_args[0][0]
    assert "Pick items>" in call_arg


@pytest.mark.asyncio
async def test_run_triage_default_prompt() -> None:
    """Default prompt should be generic, not findings-specific."""
    with patch("builtins.input", return_value="") as mock_input:
        await run_triage(["item1"])

    call_arg = mock_input.call_args[0][0]
    # The old hardcoded "findings" wording should be gone
    assert "findings" not in call_arg.lower()


# ---------------------------------------------------------------------------
# make_triage — docstring exists
# ---------------------------------------------------------------------------


def test_make_triage_has_docstring() -> None:
    assert make_triage.__doc__ is not None
    assert "items" in make_triage.__doc__.lower()


# ---------------------------------------------------------------------------
# TriageResult — docstring documents semantics
# ---------------------------------------------------------------------------


def test_triage_result_docstring_documents_indices() -> None:
    assert TriageResult.__doc__ is not None
    assert "1-based" in TriageResult.__doc__
