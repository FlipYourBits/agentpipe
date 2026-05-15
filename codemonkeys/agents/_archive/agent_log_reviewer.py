"""Agent log reviewer — evaluates whether an agent followed its instructions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition, Severity


class BehaviorFinding(BaseModel):
    category: Literal[
        "tool_scope",
        "efficiency",
        "task_completion",
        "fix_quality",
        "instruction_compliance",
    ]
    severity: Severity
    title: str
    description: str
    evidence: str | None = None


class LogReviewResult(BaseModel):
    agent_name: str
    verdict: Literal["pass", "warn", "fail"]
    tool_denials: int
    total_tool_calls: int
    findings: list[BehaviorFinding]
    recommendations: list[str]
    summary: str


_ROLE = (
    "You are an agent behavior auditor. You review event logs from completed "
    "agent runs and evaluate whether the agent followed its instructions, "
    "stayed within its tool scope, and worked efficiently."
)

_LOG_FORMAT = (
    "## Log Format\n\n"
    "The event log is JSONL (one JSON object per line). Each event has "
    "`_type`, `agent_name`, and `timestamp` fields. Key event types:\n\n"
    "- `AgentStarted` — agent run begins (`model`)\n"
    "- `ToolCall` — agent invoked a tool (`tool_name`, `tool_input`)\n"
    "- `ToolResult` — tool returned output (`tool_name`, `output`)\n"
    "- `ToolDenied` — tool call blocked by allowlist (`tool_name`, `command`)\n"
    "- `TextOutput` — agent produced text (`text`)\n"
    "- `ThinkingOutput` — agent's internal reasoning (`text`)\n"
    "- `CheckResult` — automated hook result (`command`, `passed`, `output`)\n"
    "- `TokenUpdate` — token usage after each turn (`usage`, `cost_usd`)\n"
    "- `RawMessage` — full SDK message (`message_type`, `data`)\n"
    "- `AgentCompleted` — agent finished (`result`)\n"
    "- `AgentError` — agent failed (`error`)\n\n"
    "**Reading strategy:** Start with `limit=2` on the first read — log files vary "
    "widely in size. JSONL lines containing `ToolResult` or `RawMessage` events can "
    "be extremely large (tens of thousands of tokens each) because they embed full "
    "file contents or SDK payloads. Keep `limit` at 1–2 when scanning around those "
    "events and increase only for sections with small events like `ToolCall` or "
    "`TokenUpdate`.\n"
)


def _agent_context(agent: AgentDefinition, prompt: str) -> str:
    tools_list = (
        "\n".join(f"- `{t}`" for t in agent.tools) if agent.tools else "(none)"
    )
    return (
        "## Agent Under Review\n\n"
        f"**Name:** `{agent.name}`\n"
        f"**Model:** `{agent.model}`\n\n"
        f"### Allowed Tools\n\n{tools_list}\n\n"
        f"### User Prompt\n\n{prompt}\n\n"
        f"### System Prompt\n\n{agent.system_prompt}"
    )


_REVIEW_CRITERIA = (
    "## Review Criteria\n\n"
    "Read the event log and evaluate against each criterion.\n\n"
    "### 1. Tool Scope Compliance\n"
    "- Did the agent attempt tools outside its allowed set? "
    "(ToolDenied events are direct evidence)\n"
    "- Did it try to access files outside its allowed paths?\n"
    "- Did it attempt operations it was not authorized for "
    "(git push, git commit, rm, etc.)?\n\n"
    "### 2. Efficiency\n"
    "- Did the agent waste turns on unnecessary actions — reading unrelated "
    "files, redundant reads of the same file, aimless exploration?\n"
    "- Did it go off on tangents unrelated to its task?\n"
    "- Was the turn count reasonable for the scope of work?\n\n"
    "### 3. Task Completion\n"
    "- Did the agent actually do what its prompt asked?\n"
    "- For auditor/fixer agents: did it read the target, identify real issues, "
    "and apply fixes?\n"
    "- For reviewer agents: did it produce meaningful findings?\n\n"
    "### 4. Fix Quality (for agents that edit files)\n"
    "- Did Edit calls target real issues, not cosmetic noise?\n"
    "- Were edits correct and complete?\n"
    "- Did the agent verify its fixes (e.g., re-read after editing)?\n\n"
    "### 5. Instruction Compliance\n"
    "- Did the agent follow the specific rules in its system prompt?\n"
    "- Did it respect constraints (e.g., 'do not push', 'only edit this file')?\n"
)

_OUTPUT_INSTRUCTIONS = (
    "## Output\n\n"
    "Set `verdict` to:\n"
    "- `pass` — agent behaved correctly with no significant issues\n"
    "- `warn` — minor issues but overall acceptable behavior\n"
    "- `fail` — significant behavioral problems\n\n"
    "Use these finding categories:\n"
    "- `tool_scope` — tool or path access violations\n"
    "- `efficiency` — wasted turns or unnecessary actions\n"
    "- `task_completion` — failed to complete assigned work\n"
    "- `fix_quality` — edits were incorrect, incomplete, or cosmetic noise\n"
    "- `instruction_compliance` — violated explicit instructions\n\n"
    "Use `evidence` to quote the specific log line(s) that support the finding.\n"
    "Only report findings you are confident about — do not speculate.\n"
    "If the agent behaved well, return an empty findings list with verdict `pass`.\n\n"
    "For `recommendations`, write actionable changes to the agent's definition "
    "(system prompt wording, tool scope, model choice, etc.) that would prevent "
    "the findings from recurring. Each recommendation should be a single concise "
    "sentence. Leave the list empty if there are no findings."
)


def _build_system_prompt(agent: AgentDefinition, prompt: str) -> str:
    return "\n\n".join([
        _ROLE,
        _LOG_FORMAT,
        _agent_context(agent, prompt),
        _REVIEW_CRITERIA,
        _OUTPUT_INSTRUCTIONS,
    ])


def make_agent_log_reviewer(
    log_file: str, agent: AgentDefinition, prompt: str
) -> AgentDefinition:
    """Build an AgentDefinition that reviews an agent's event log for behavioral issues."""
    return AgentDefinition(
        name=f"agent_log_reviewer:{agent.name}",
        model="sonnet",
        system_prompt=_build_system_prompt(agent, prompt),
        tools=[f"Read({log_file})"],
        output_schema=LogReviewResult,
    )
