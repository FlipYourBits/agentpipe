# codemonkeys

Agent workflows for Python development, powered by the [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-agent-sdk). Structured code review via parallel agents, automated fixing, and engineering standards — all orchestrated from the command line.

## Why codemonkeys over a Claude Code session?

A Claude Code session is a single conversational thread with full permissions, no enforced structure, and whatever the human remembers to ask for. Codemonkeys provides **constrained, repeatable, parallelizable agent pipelines with automated quality gates.**

- **Scoped agents that can't go off-script** — tool restrictions, filesystem sandboxing, and pattern-matched permissions. A code reviewer can't write files. A test writer can't touch source. Trust boundaries within a workflow, not "Claude has access to everything."
- **Parallel execution** — review 10 files simultaneously, run test writers across uncovered modules. A Claude Code session is inherently sequential. This is where you get actual throughput gains.
- **Encoded process as code** — stop hooks gate completion on passing tests, post-edit auto-linting, review checklists applied consistently every run. Engineering standards are versioned, shared, and enforced — not dependent on the human remembering to say "also run the linter."

## Quickstart

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/), and a Claude API key (`ANTHROPIC_API_KEY`).

```bash
# Install the CLI globally
uv tool install codemonkeys --from git+https://github.com/FlipYourBits/codemonkeys.git

# In your project directory, install Claude Code skills
cd your-project/
codemonkeys init
```

That's it — `codemonkeys` is on your PATH and Claude Code picks up the skills automatically.

## Usage

### Review workflow

Review all Python files matching a glob pattern, triage findings interactively, and optionally apply fixes:

```bash
# Review specific files or directories
codemonkeys review src/foo.py src/bar.py
codemonkeys review src/core/

# Review changes against a git ref
codemonkeys review --diff
codemonkeys review --diff main
```

The workflow runs through three stages:

1. **Review** — dispatches a reviewer agent per file in parallel (up to 5 concurrent). Each agent returns structured JSON findings covering code quality, security, and Python conventions.
2. **Triage** — presents all findings and lets you select which to fix.
3. **Fix** — applies the selected fixes via a python fixer agent.

### Research

Dispatch an Opus-powered agent that searches the web, reads papers/docs/repos/forums, verifies claims with a confidence system, and writes a SKILL.md or markdown report:

```bash
# Research a topic and generate a Claude SKILL.md
codemonkeys research 'flux.1 image generation https://arxiv.org/html/2408.06072'

# Generate a markdown report instead
codemonkeys research 'UXP plugins for Photoshop 2025' --format markdown
```

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
  agents/          # Agent factories — each returns an AgentDefinition (includes researcher.py)
  core/
    runner.py      # run_agent(): wraps claude_agent_sdk.query()
    types.py       # AgentDefinition, RunResult, TokenUsage
    events.py      # Typed event system (AgentStarted, ToolCall, etc.)
    hooks.py       # Tool permission enforcement + automated checks
    sandbox.py     # OS-level filesystem sandboxing
    discovery.py   # File discovery by glob pattern
  display/         # file_printer, stdout formatting, file logging
  prompts/         # Shared prompt templates (quality, security, guidelines)
```

### Agents

| Agent | Purpose | Model |
|-------|---------|-------|
| `python_file_reviewer` | Per-file code quality, security, and conventions review | sonnet |
| `python_file_editor` | Per-file code edits and fixes | sonnet |
| `python_architecture_reviewer` | Cross-file design review | opus |
| `researcher` | Autonomous web research with structured output | opus |

### Key concepts

**AgentDefinition** — immutable dataclass describing an agent: name, model, system prompt, allowed tools, output schema, hooks, and `max_stop_retries` (default 2, caps consecutive Stop-hook failures).

**Hooks** — shell commands that run automatically at SDK hook events. `PreToolUse` hooks enforce tool permissions. `PostToolUse` hooks run checks after tool calls (e.g., ruff after edits). `Stop` hooks gate agent completion (e.g., tests must pass).

**Events** — typed dataclasses emitted during agent runs (`AgentStarted`, `ToolCall`, `TokenUpdate`, etc.). Handlers can log, display, or react to events.

**Sandbox** — OS-level filesystem restriction. Once activated, the process can only write inside the project directory. Backends: Landlock (Linux), sandbox-exec (macOS), Low Integrity Token (Windows).

## Development

```bash
git clone https://github.com/FlipYourBits/codemonkeys.git
cd codemonkeys
uv sync --extra dev
uv tool install -e . --force
```

The `-e` (editable) flag links the global `codemonkeys` CLI to your local source — code changes are picked up immediately without reinstalling.

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
