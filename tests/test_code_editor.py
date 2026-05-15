"""Tests for codemonkeys/agents/code_editor.py."""

from __future__ import annotations

import pytest

from codemonkeys.agents.code_editor import make_code_editor
from codemonkeys.core.types import AgentDefinition


# --- Agent definition basics ---


def test_returns_agent_definition() -> None:
    agent = make_code_editor("src/app.py", task="Fix naming issue", task_type="fix")
    assert isinstance(agent, AgentDefinition)


def test_model_is_sonnet() -> None:
    agent = make_code_editor("src/app.py", task="Fix it", task_type="fix")
    assert agent.model == "sonnet"


def test_name_format() -> None:
    agent = make_code_editor("codemonkeys/cli.py", task="t", task_type="fix")
    assert agent.name == "code_editor:fix:cli.py"


def test_name_format_feat() -> None:
    agent = make_code_editor("src/new.py", task="t", task_type="feat")
    assert agent.name == "code_editor:feat:new.py"


def test_name_format_test() -> None:
    agent = make_code_editor("tests/test_x.py", task="t", task_type="test")
    assert agent.name == "code_editor:test:test_x.py"


def test_no_output_schema() -> None:
    agent = make_code_editor("x.py", task="t", task_type="fix")
    assert agent.output_schema is None


def test_task_in_system_prompt() -> None:
    agent = make_code_editor("x.py", task="Rename variable foo to bar", task_type="fix")
    assert "Rename variable foo to bar" in agent.system_prompt


# --- Tool selection by task_type ---


def test_fix_tools_read_and_edit_only() -> None:
    agent = make_code_editor("src/app.py", task="t", task_type="fix")
    assert "Read(src/app.py)" in agent.tools
    assert "Edit(src/app.py)" in agent.tools
    assert "Write(src/app.py)" not in agent.tools


def test_refactor_tools_read_and_edit_only() -> None:
    agent = make_code_editor("src/app.py", task="t", task_type="refactor")
    assert "Read(src/app.py)" in agent.tools
    assert "Edit(src/app.py)" in agent.tools
    assert "Write(src/app.py)" not in agent.tools


def test_feat_tools_include_write() -> None:
    agent = make_code_editor("src/new.py", task="t", task_type="feat")
    assert "Read(src/new.py)" in agent.tools
    assert "Edit(src/new.py)" in agent.tools
    assert "Write(src/new.py)" in agent.tools


def test_test_tools_include_write() -> None:
    agent = make_code_editor("tests/test_x.py", task="t", task_type="test")
    assert "Write(tests/test_x.py)" in agent.tools


def test_docs_tools_include_write() -> None:
    agent = make_code_editor("docs/api.md", task="t", task_type="docs")
    assert "Write(docs/api.md)" in agent.tools


# --- read_paths ---


def test_read_paths_adds_read_tools() -> None:
    agent = make_code_editor(
        "src/app.py", task="t", task_type="feat",
        read_paths=["src/types.py", "src/utils.py"],
    )
    assert "Read(src/types.py)" in agent.tools
    assert "Read(src/utils.py)" in agent.tools


def test_read_paths_none_is_fine() -> None:
    agent = make_code_editor("src/app.py", task="t", task_type="fix")
    assert len(agent.tools) == 2


def test_read_paths_empty_list() -> None:
    agent = make_code_editor("src/app.py", task="t", task_type="fix", read_paths=[])
    assert len(agent.tools) == 2


# --- Invalid task_type ---


def test_invalid_task_type_raises() -> None:
    with pytest.raises(ValueError):
        make_code_editor("x.py", task="t", task_type="deploy")


# --- Multi-file support ---


def test_multi_file_name_format() -> None:
    agent = make_code_editor(["a.py", "b.py", "c.py"], task="t", task_type="refactor")
    assert agent.name == "code_editor:refactor:3_files"


def test_multi_file_read_and_edit_for_each() -> None:
    agent = make_code_editor(["src/a.py", "src/b.py"], task="t", task_type="fix")
    assert "Read(src/a.py)" in agent.tools
    assert "Read(src/b.py)" in agent.tools
    assert "Edit(src/a.py)" in agent.tools
    assert "Edit(src/b.py)" in agent.tools
    assert "Write(src/a.py)" not in agent.tools


def test_multi_file_feat_includes_write_for_all() -> None:
    agent = make_code_editor(["a.py", "b.py"], task="t", task_type="feat")
    assert "Write(a.py)" in agent.tools
    assert "Write(b.py)" in agent.tools


def test_multi_file_with_read_paths() -> None:
    agent = make_code_editor(
        ["a.py", "b.py"], task="t", task_type="fix",
        read_paths=["types.py"],
    )
    assert "Read(types.py)" in agent.tools
    assert "Edit(a.py)" in agent.tools
    assert "Edit(b.py)" in agent.tools


def test_multi_file_system_prompt_lists_all_files() -> None:
    agent = make_code_editor(["a.py", "b.py"], task="t", task_type="fix")
    assert "`a.py`" in agent.system_prompt
    assert "`b.py`" in agent.system_prompt


def test_single_file_as_list_works() -> None:
    agent = make_code_editor(["src/app.py"], task="t", task_type="fix")
    assert agent.name == "code_editor:fix:app.py"
    assert "Read(src/app.py)" in agent.tools


# --- Language auto-detection ---


def test_python_file_gets_python_guidelines() -> None:
    agent = make_code_editor("src/app.py", task="t", task_type="fix")
    assert "from __future__ import annotations" in agent.system_prompt


def test_unknown_extension_gets_engineering_guidelines_only() -> None:
    agent = make_code_editor("src/app.xyz", task="t", task_type="fix")
    assert "Engineering Mindset" in agent.system_prompt
    assert "from __future__" not in agent.system_prompt


def test_multi_file_mixed_extensions_gets_all_guidelines() -> None:
    agent = make_code_editor(["a.py", "b.py", "c.xyz"], task="t", task_type="fix")
    assert "from __future__ import annotations" in agent.system_prompt
    assert "Engineering Mindset" in agent.system_prompt


def test_multi_file_same_extension_no_duplicate_guidelines() -> None:
    agent = make_code_editor(["a.py", "b.py"], task="t", task_type="fix")
    count = agent.system_prompt.count("from __future__ import annotations")
    assert count == 1
