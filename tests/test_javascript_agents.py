"""Tests for JavaScript/TypeScript agent support."""

from __future__ import annotations

from codemonkeys.agents import REVIEWERS, get_reviewer
from codemonkeys.agents.code_editor import make_code_editor
from codemonkeys.agents.code_reviewer import (
    get_language_config,
    make_code_reviewer,
)
from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import JAVASCRIPT_GUIDELINES


JS_EXTENSIONS = [".js", ".ts", ".jsx", ".tsx"]


class TestGuidelinesContent:
    def test_guidelines_mentions_const(self) -> None:
        assert "const" in JAVASCRIPT_GUIDELINES

    def test_guidelines_mentions_async_await(self) -> None:
        assert "async" in JAVASCRIPT_GUIDELINES
        assert "await" in JAVASCRIPT_GUIDELINES

    def test_guidelines_mentions_typescript(self) -> None:
        assert "TypeScript" in JAVASCRIPT_GUIDELINES

    def test_guidelines_mentions_strict_equality(self) -> None:
        assert "===" in JAVASCRIPT_GUIDELINES


class TestLanguageConfig:
    def test_js_returns_javascript(self) -> None:
        name, guidelines = get_language_config(".js")
        assert name == "JavaScript"
        assert guidelines is not None

    def test_jsx_returns_javascript(self) -> None:
        name, guidelines = get_language_config(".jsx")
        assert name == "JavaScript"
        assert guidelines is not None

    def test_ts_returns_typescript(self) -> None:
        name, guidelines = get_language_config(".ts")
        assert name == "TypeScript"
        assert guidelines is not None

    def test_tsx_returns_typescript(self) -> None:
        name, guidelines = get_language_config(".tsx")
        assert name == "TypeScript"
        assert guidelines is not None

    def test_all_extensions_share_same_guidelines(self) -> None:
        guidelines_set = set()
        for ext in JS_EXTENSIONS:
            _, guidelines = get_language_config(ext)
            guidelines_set.add(guidelines)
        assert len(guidelines_set) == 1


class TestReviewerRegistry:
    def test_all_extensions_registered(self) -> None:
        for ext in JS_EXTENSIONS:
            assert ext in REVIEWERS, f"{ext} not in REVIEWERS"

    def test_get_reviewer_returns_factory(self) -> None:
        for ext in JS_EXTENSIONS:
            assert get_reviewer(ext) is not None, f"get_reviewer({ext}) returned None"


class TestCodeReviewer:
    def test_reviewer_returns_agent_definition(self) -> None:
        agent = make_code_reviewer("app.ts")
        assert isinstance(agent, AgentDefinition)

    def test_reviewer_system_prompt_contains_guidelines(self) -> None:
        agent = make_code_reviewer("app.ts")
        assert "const" in agent.system_prompt
        assert "TypeScript" in agent.system_prompt

    def test_reviewer_name_includes_filename(self) -> None:
        agent = make_code_reviewer("src/utils.js")
        assert "utils.js" in agent.name

    def test_reviewer_jsx_file(self) -> None:
        agent = make_code_reviewer("Component.jsx")
        assert isinstance(agent, AgentDefinition)
        assert "JavaScript" in agent.system_prompt

    def test_reviewer_tsx_file(self) -> None:
        agent = make_code_reviewer("Component.tsx")
        assert isinstance(agent, AgentDefinition)
        assert "TypeScript" in agent.system_prompt


class TestCodeEditor:
    def test_editor_includes_js_guidelines(self) -> None:
        agent = make_code_editor("app.ts", task="fix bug", task_type="fix")
        assert "const" in agent.system_prompt

    def test_editor_mixed_extensions(self) -> None:
        agent = make_code_editor(
            ["app.ts", "utils.py"],
            task="refactor",
            task_type="refactor",
        )
        assert "const" in agent.system_prompt
        assert "f-strings" in agent.system_prompt

    def test_editor_jsx_includes_guidelines(self) -> None:
        agent = make_code_editor("App.jsx", task="fix bug", task_type="fix")
        assert "const" in agent.system_prompt
