"""Tests for codemonkeys/agents/code_reviewer.py."""

from __future__ import annotations

from codemonkeys.agents.code_reviewer import (
    _GUIDELINES,
    get_language_config,
    make_code_reviewer,
)
from codemonkeys.core.types import AgentDefinition, FileReviewResult


def test_returns_agent_definition() -> None:
    agent = make_code_reviewer("codemonkeys/cli.py")
    assert isinstance(agent, AgentDefinition)


def test_model_is_sonnet() -> None:
    agent = make_code_reviewer("codemonkeys/cli.py")
    assert agent.model == "sonnet"


def test_tools_read_only() -> None:
    agent = make_code_reviewer("codemonkeys/cli.py")
    assert agent.tools == ["Read(codemonkeys/cli.py)"]


def test_no_edit_or_write_tools() -> None:
    agent = make_code_reviewer("src/app.py")
    for tool in agent.tools:
        assert not tool.startswith("Edit(")
        assert not tool.startswith("Write(")


def test_output_schema_is_file_review_result() -> None:
    agent = make_code_reviewer("x.py")
    assert agent.output_schema is FileReviewResult


def test_name_includes_filename() -> None:
    agent = make_code_reviewer("codemonkeys/core/runner.py")
    assert agent.name == "code_reviewer:runner.py"


def test_system_prompt_contains_file_path() -> None:
    agent = make_code_reviewer("codemonkeys/cli.py")
    assert "codemonkeys/cli.py" in agent.system_prompt


def test_system_prompt_contains_read_only_instruction() -> None:
    agent = make_code_reviewer("x.py")
    prompt = agent.system_prompt.lower()
    assert "do not" in prompt and ("edit" in prompt or "modify" in prompt)


def test_system_prompt_contains_review_checklists() -> None:
    agent = make_code_reviewer("x.py")
    assert "naming" in agent.system_prompt
    assert "function_design" in agent.system_prompt
    assert "security" in agent.system_prompt.lower()


def test_system_prompt_contains_design_review() -> None:
    agent = make_code_reviewer("x.py")
    assert "paradigm_inconsistency" in agent.system_prompt
    assert "layer_violation" in agent.system_prompt
    assert "dependency_coupling" in agent.system_prompt


def test_deny_hint_present() -> None:
    agent = make_code_reviewer("x.py")
    assert agent.deny_hint is not None


def test_python_file_gets_python_role() -> None:
    agent = make_code_reviewer("src/app.py")
    assert "Python code reviewer" in agent.system_prompt


def test_python_file_gets_python_guidelines() -> None:
    agent = make_code_reviewer("src/app.py")
    assert "from __future__ import annotations" in agent.system_prompt


def test_unknown_extension_gets_general_role() -> None:
    agent = make_code_reviewer("src/app.xyz")
    assert "general code reviewer" in agent.system_prompt


def test_unknown_extension_no_language_guidelines() -> None:
    agent = make_code_reviewer("src/app.xyz")
    assert "from __future__" not in agent.system_prompt


def test_get_language_known_extension() -> None:
    name, guidelines = get_language_config(".py")
    assert name == "Python"
    assert guidelines is not None


def test_get_language_unknown_extension() -> None:
    name, guidelines = get_language_config(".xyz")
    assert name == "general"
    assert guidelines is None


def test_python_registered_in_guidelines() -> None:
    assert ".py" in _GUIDELINES
