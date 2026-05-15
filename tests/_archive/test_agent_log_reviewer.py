"""Tests for agent_log_reviewer agent module."""

from __future__ import annotations

from codemonkeys.agents.agent_log_reviewer import (
    BehaviorFinding,
    LogReviewResult,
    make_agent_log_reviewer,
)
from codemonkeys.core.types import AgentDefinition


def _stub_agent() -> AgentDefinition:
    return AgentDefinition(
        name="python_file_auditor:example.py",
        model="opus",
        system_prompt="You are an auditor. Review and fix example.py.",
        tools=["Read(example.py)", "Edit(example.py)"],
    )


# ---------------------------------------------------------------------------
# make_agent_log_reviewer — returns AgentDefinition
# ---------------------------------------------------------------------------


def test_returns_agent_definition() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert isinstance(agent, AgentDefinition)


def test_name_includes_reviewed_agent() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert agent.name == "agent_log_reviewer:python_file_auditor:example.py"


def test_model_is_sonnet() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert agent.model == "sonnet"


def test_tools_scoped_to_log_file() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert agent.tools == ["Read(/tmp/log.jsonl)"]


def test_output_schema_is_log_review_result() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert agent.output_schema is LogReviewResult


# ---------------------------------------------------------------------------
# make_agent_log_reviewer — system prompt contents
# ---------------------------------------------------------------------------


def test_prompt_contains_reviewed_agent_name() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "python_file_auditor:example.py" in agent.system_prompt


def test_prompt_contains_reviewed_agent_tools() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "Read(example.py)" in agent.system_prompt
    assert "Edit(example.py)" in agent.system_prompt


def test_prompt_contains_user_prompt() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "Audit this file." in agent.system_prompt


def test_prompt_contains_reviewed_agent_system_prompt() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "You are an auditor. Review and fix example.py." in agent.system_prompt


def test_prompt_contains_log_format_reference() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "ToolCall" in agent.system_prompt
    assert "ToolDenied" in agent.system_prompt
    assert "JSONL" in agent.system_prompt


def test_prompt_contains_review_criteria() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "Tool Scope Compliance" in agent.system_prompt
    assert "Efficiency" in agent.system_prompt
    assert "Task Completion" in agent.system_prompt
    assert "Fix Quality" in agent.system_prompt
    assert "Instruction Compliance" in agent.system_prompt


def test_prompt_contains_verdict_definitions() -> None:
    agent = make_agent_log_reviewer("/tmp/log.jsonl", _stub_agent(), "Audit this file.")
    assert "`pass`" in agent.system_prompt
    assert "`warn`" in agent.system_prompt
    assert "`fail`" in agent.system_prompt


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


def test_behavior_finding_valid() -> None:
    f = BehaviorFinding(
        category="tool_scope",
        severity="high",
        title="Attempted unauthorized tool",
        description="Agent tried to use Bash but only had Read/Edit.",
        evidence='{"_type": "ToolDenied", "tool_name": "Bash"}',
    )
    assert f.category == "tool_scope"
    assert f.severity == "high"


def test_behavior_finding_evidence_optional() -> None:
    f = BehaviorFinding(
        category="efficiency",
        severity="low",
        title="Redundant read",
        description="Agent read the same file three times.",
    )
    assert f.evidence is None


def test_log_review_result_pass() -> None:
    r = LogReviewResult(
        agent_name="python_file_auditor:example.py",
        verdict="pass",
        tool_denials=0,
        total_tool_calls=4,
        findings=[],
        recommendations=[],
        summary="Agent behaved correctly.",
    )
    assert r.verdict == "pass"
    assert r.findings == []
    assert r.recommendations == []


def test_log_review_result_with_findings() -> None:
    r = LogReviewResult(
        agent_name="python_file_auditor:example.py",
        verdict="fail",
        tool_denials=2,
        total_tool_calls=10,
        findings=[
            BehaviorFinding(
                category="tool_scope",
                severity="high",
                title="Denied tool attempts",
                description="Agent tried Bash twice and was denied.",
            ),
        ],
        recommendations=[
            "Add an explicit rule to the system prompt: 'Do not use Bash.'",
        ],
        summary="Agent violated tool scope.",
    )
    assert r.verdict == "fail"
    assert len(r.findings) == 1
    assert r.tool_denials == 2
    assert len(r.recommendations) == 1


def test_agent_with_no_tools_shows_none_in_prompt() -> None:
    bare_agent = AgentDefinition(
        name="triage",
        model="haiku",
        system_prompt="You triage.",
        tools=[],
    )
    reviewer = make_agent_log_reviewer("/tmp/log.jsonl", bare_agent, "Triage this.")
    assert "(none)" in reviewer.system_prompt
