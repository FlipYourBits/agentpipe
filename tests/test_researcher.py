"""Tests for codemonkeys/agents/researcher.py."""

from __future__ import annotations

from codemonkeys.agents.researcher import make_researcher, make_topic_slug
from codemonkeys.core.types import AgentDefinition


def test_returns_agent_definition() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert isinstance(agent, AgentDefinition)


def test_model_is_opus() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert agent.model == "opus"


def test_tools_include_web_and_write() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    tool_names = [t.split("(")[0] for t in agent.tools]
    assert "WebFetch" in tool_names
    assert "WebSearch" in tool_names
    assert "Write" in tool_names


def test_write_tool_scoped_to_output_path() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    write_tools = [t for t in agent.tools if t.startswith("Write(")]
    assert len(write_tools) == 1
    assert "Write(/tmp/out.md)" in write_tools


def test_no_output_schema() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert agent.output_schema is None


def test_no_deny_hint() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert agent.deny_hint is None


def test_name_includes_researcher() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert "researcher" in agent.name


def test_system_prompt_contains_methodology() -> None:
    agent = make_researcher("test topic", "/tmp/out.md")
    assert "Research Methodology" in agent.system_prompt
    assert "Verification Rules" in agent.system_prompt


def test_system_prompt_contains_skill_format() -> None:
    agent = make_researcher("test topic", "/tmp/out.md", output_format="skill")
    assert "SKILL.md" in agent.system_prompt
    assert "frontmatter" in agent.system_prompt.lower()


def test_system_prompt_contains_report_format() -> None:
    agent = make_researcher("test topic", "/tmp/out.md", output_format="markdown")
    assert "Markdown Report" in agent.system_prompt
    assert "Executive Summary" in agent.system_prompt


def test_system_prompt_contains_output_path() -> None:
    agent = make_researcher("test topic", "/tmp/custom/path.md")
    assert "/tmp/custom/path.md" in agent.system_prompt


def test_slug_basic() -> None:
    assert make_topic_slug("flux.1 image generation") == "flux1-image-generation"


def test_slug_strips_urls() -> None:
    slug = make_topic_slug("flux.1 image generation https://arxiv.org/html/2408.06072")
    assert "arxiv" not in slug
    assert "http" not in slug


def test_slug_limits_length() -> None:
    slug = make_topic_slug("a very long topic with many words that should be truncated")
    word_count = len(slug.split("-"))
    assert word_count <= 5


def test_slug_lowercases() -> None:
    slug = make_topic_slug("UXP Plugins for Photoshop 2025")
    assert slug == slug.lower()


def test_slug_handles_special_chars() -> None:
    slug = make_topic_slug("C++ best practices & patterns")
    assert "&" not in slug
    assert "+" not in slug
