# codemonkeys

Agent workflows for Python development, powered by the [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-agent-sdk). Structured code review via parallel agents, automated fixing, and engineering standards — all orchestrated from the command line.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- A Claude API key (`ANTHROPIC_API_KEY`)

## Installation

```bash
git clone https://github.com/FlipYourBits/codemonkeys.git
cd codemonkeys
uv sync --extra dev
```

## Usage

### Review workflow

Review all Python files matching a glob pattern, triage findings interactively, and optionally apply fixes:

```bash
# Review all Python files in the project
uv run python -m codemonkeys.workflows.review

# Review files matching a pattern
uv run python -m codemonkeys.workflows.review 'codemonkeys/core/**/*.py'
```

The workflow runs through three stages:

1. **Review** — dispatches a reviewer agent per file in parallel (up to 5 concurrent). Each agent returns structured JSON findings covering code quality, security, and Python conventions.
2. **Triage** — presents all findings and lets you select which to fix.
3. **Fix** — applies the selected fixes via a fixer agent.

### Using the library

```python
from codemonkeys import AgentDefinition, RunResult, run_agent

agent = AgentDefinition(
    name="my-agent",
    model="sonnet",
    system_prompt="You are a helpful assistant.",
    allowed_tools=["Read", "Bash(git log*)"],
    hooks={
        "PostToolUse": [("Edit", "uv run ruff check --fix {file_path}")],
        "Stop": [(None, "uv run pytest -x -q --tb=short")],
    },
)

result = await run_agent(agent, "Review this file.", on_event=my_handler)
```

## Architecture

```
codemonkeys/
  agents/          # Agent factories — each returns an AgentDefinition
  core/
    runner.py      # run_agent(): wraps claude_agent_sdk.query()
    types.py       # AgentDefinition, RunResult, TokenUsage
    events.py      # Typed event system (AgentStarted, ToolCall, etc.)
    hooks.py       # Tool permission enforcement + automated checks
    sandbox.py     # OS-level filesystem sandboxing
    discovery.py   # File discovery by glob pattern
  display/         # Rich live display, stdout formatting, file logging
  prompts/         # Shared prompt templates (quality, security, guidelines)
  workflows/       # Multi-agent orchestration (review pipeline)
```

### Agents

| Agent | Purpose | Model |
|-------|---------|-------|
| `python_reviewer` | Per-file code quality, security, and conventions review | sonnet |
| `architecture_reviewer` | Cross-file design review | opus |
| `fixer` | Applies fixes from triaged findings | sonnet |
| `triage` | Prioritizes and filters findings | sonnet |
| `python_implementer` | TDD implementation from a plan file | opus |
| `changelog_reviewer` | CHANGELOG.md vs git history accuracy | haiku |
| `readme_reviewer` | Verifies README claims against codebase | sonnet |

### Key concepts

**AgentDefinition** — immutable dataclass describing an agent: name, model, system prompt, allowed tools, output schema, and hooks.

**Hooks** — shell commands that run automatically at SDK hook events. `PreToolUse` hooks enforce tool permissions. `PostToolUse` hooks run checks after tool calls (e.g., ruff after edits). `Stop` hooks gate agent completion (e.g., tests must pass).

**Events** — typed dataclasses emitted during agent runs (`AgentStarted`, `ToolCall`, `TokenUpdate`, etc.). Handlers can log, display, or react to events.

**Sandbox** — OS-level filesystem restriction. Once activated, the process can only write inside the project directory. Backends: Landlock (Linux), sandbox-exec (macOS), Low Integrity Token (Windows).

## Development

```bash
# Run tests
uv run pytest

# Lint and format
uv run ruff check --fix . && uv run ruff format .

# Type check
uv run pyright .
```

## License

[MIT](LICENSE)
