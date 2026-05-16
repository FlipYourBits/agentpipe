"""Tests for HTML and CSS agent support."""

from __future__ import annotations

from codemonkeys.agents import REVIEWERS, get_reviewer
from codemonkeys.agents.code_editor import make_code_editor
from codemonkeys.agents.code_reviewer import (
    get_language_config,
    make_code_reviewer,
)
from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import CSS_GUIDELINES, HTML_GUIDELINES, JAVASCRIPT_GUIDELINES


class TestHtmlGuidelinesContent:
    def test_mentions_semantic_elements(self) -> None:
        assert "semantic" in HTML_GUIDELINES

    def test_mentions_accessibility(self) -> None:
        assert "alt" in HTML_GUIDELINES

    def test_mentions_xss(self) -> None:
        assert "XSS" in HTML_GUIDELINES

    def test_mentions_aria(self) -> None:
        assert "ARIA" in HTML_GUIDELINES


class TestCssGuidelinesContent:
    def test_mentions_specificity(self) -> None:
        assert "specificity" in CSS_GUIDELINES.lower()

    def test_mentions_custom_properties(self) -> None:
        assert "custom properties" in CSS_GUIDELINES

    def test_mentions_flexbox(self) -> None:
        assert "flexbox" in CSS_GUIDELINES

    def test_mentions_reduced_motion(self) -> None:
        assert "prefers-reduced-motion" in CSS_GUIDELINES


class TestHtmlLanguageConfig:
    def test_html_returns_html_name(self) -> None:
        name, guidelines = get_language_config(".html")
        assert name == "HTML"
        assert guidelines is not None

    def test_html_guidelines_contain_html_content(self) -> None:
        _, guidelines = get_language_config(".html")
        assert "semantic" in guidelines

    def test_html_guidelines_contain_js_content(self) -> None:
        _, guidelines = get_language_config(".html")
        assert "const" in guidelines

    def test_html_guidelines_contain_css_content(self) -> None:
        _, guidelines = get_language_config(".html")
        assert "specificity" in guidelines.lower()


class TestCssLanguageConfig:
    def test_css_returns_css_name(self) -> None:
        name, guidelines = get_language_config(".css")
        assert name == "CSS"
        assert guidelines is not None

    def test_css_guidelines_contain_css_content(self) -> None:
        _, guidelines = get_language_config(".css")
        assert "custom properties" in guidelines

    def test_css_guidelines_do_not_contain_js_content(self) -> None:
        _, guidelines = get_language_config(".css")
        assert "async" not in guidelines
        assert "await" not in guidelines

    def test_css_guidelines_do_not_contain_html_content(self) -> None:
        _, guidelines = get_language_config(".css")
        assert "semantic" not in guidelines


class TestReviewerRegistry:
    def test_html_registered(self) -> None:
        assert ".html" in REVIEWERS

    def test_css_registered(self) -> None:
        assert ".css" in REVIEWERS

    def test_get_reviewer_html(self) -> None:
        assert get_reviewer(".html") is not None

    def test_get_reviewer_css(self) -> None:
        assert get_reviewer(".css") is not None


class TestCodeReviewer:
    def test_reviewer_html_returns_agent_definition(self) -> None:
        agent = make_code_reviewer("index.html")
        assert isinstance(agent, AgentDefinition)

    def test_reviewer_html_prompt_contains_composite(self) -> None:
        agent = make_code_reviewer("index.html")
        assert "semantic" in agent.system_prompt
        assert "const" in agent.system_prompt
        assert "specificity" in agent.system_prompt.lower()

    def test_reviewer_css_returns_agent_definition(self) -> None:
        agent = make_code_reviewer("styles.css")
        assert isinstance(agent, AgentDefinition)

    def test_reviewer_css_prompt_contains_css_only(self) -> None:
        agent = make_code_reviewer("styles.css")
        assert "custom properties" in agent.system_prompt
        assert "semantic" not in agent.system_prompt


class TestCodeEditor:
    def test_editor_html_includes_composite_guidelines(self) -> None:
        agent = make_code_editor("index.html", task="fix bug", task_type="fix")
        assert "semantic" in agent.system_prompt
        assert "const" in agent.system_prompt
        assert "specificity" in agent.system_prompt.lower()

    def test_editor_css_includes_css_guidelines(self) -> None:
        agent = make_code_editor("styles.css", task="fix bug", task_type="fix")
        assert "custom properties" in agent.system_prompt

    def test_editor_mixed_html_and_py(self) -> None:
        agent = make_code_editor(
            ["index.html", "app.py"],
            task="refactor",
            task_type="refactor",
        )
        assert "semantic" in agent.system_prompt
        assert "f-strings" in agent.system_prompt
