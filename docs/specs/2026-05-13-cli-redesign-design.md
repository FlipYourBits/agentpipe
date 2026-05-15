# CLI Redesign: Generic File Audit Dispatcher

Date: 2026-05-13
Status: approved

## Goal

Replace the multi-workflow CLI with a single `codemonkeys audit` command that discovers files, routes to the right agent factory by extension, and runs agents in parallel. Delete everything else.

## Context

The current CLI has four commands (audit, bugfix, feature, commit) backed by workflow modules that orchestrate multi-phase pipelines. The workflows add complexity (pre-flight checks, architecture review, test verification, interactive planning, iteration loops, checkpoint/resume) that isn't needed for the core use case: run an agent on each file, show what changed.

The file auditor pattern (factory takes a file path, reads content, agent fixes it, runner captures .patch) is the gold standard. The CLI should be a thin dispatcher that leverages this pattern.

## CLI Interface

```
codemonkeys audit **/*.py
codemonkeys audit codemonkeys/agents/*.py codemonkeys/core/*.py
codemonkeys audit --diff
codemonkeys audit --diff --max-parallel 8
```

- **Positional args**: glob patterns. Required unless `--diff` is used.
- `--diff`: audit files changed on the current branch (vs default remote branch). Can combine with patterns to filter.
- `--max-parallel N`: concurrency limit. Default 4, overridable via `CODEMONKEYS_MAX_PARALLEL_AGENTS` env var. CLI flag takes precedence.

No other commands. No subcommands. `codemonkeys audit` is the only entry point.

## Agent Registry

A plain dict in `agents/__init__.py` mapping file extensions to factory functions:

```python
AUDITORS: dict[str, Callable[[str], AgentDefinition]] = {
    ".py": make_python_file_auditor,
}

def get_auditor(ext: str) -> Callable[[str], AgentDefinition] | None:
    return AUDITORS.get(ext)
```

Each factory has the signature `(file: str) -> AgentDefinition`. The factory reads the file internally.

When files have an extension not in the registry, print a warning (`No auditor for .js files, skipping 12 files`) and continue with files that have agents.

## Flow

1. Parse CLI args (argparse)
2. Discover files: expand glob patterns, or get changed files from `--diff`
3. Group files by extension (using `Path(f).suffix`)
4. For each extension group:
   - Look up `AUDITORS[ext]` via `get_auditor(ext)`
   - If missing, warn and skip
5. Flatten all auditable files into a single list
6. If no auditable files, print message and exit
7. Run agents in parallel:
   - `asyncio.Semaphore(max_parallel)` limits concurrency
   - Each agent gets a `logged()` context (stdout printer + JSONL file logger)
   - `asyncio.gather()` runs all tasks
8. As each agent completes, print status: `OK/FAIL filepath (N/total)`
9. Print summary: files audited, errors, total cost

## Display

Reuse the existing display layer unchanged:

- `display/stdout.py` — `make_stdout_printer()` shows live spinner, tool calls, token usage, cost per turn
- `display/logger.py` — `logged()` context manager combines stdout printer with JSONL file logging
- Log directory created via `make_log_dir("audit")`

## What Gets Deleted

### Files to delete

- `codemonkeys/workflows/audit.py`
- `codemonkeys/workflows/bugfix.py`
- `codemonkeys/workflows/feature.py`
- `codemonkeys/workflows/commit.py`
- `codemonkeys/workflows/__init__.py`
- `tests/test_audit.py` (tests the old audit workflow)
- `tests/test_audit_workflow.py`
- `tests/test_bugfix.py`
- `tests/test_python_bug_fix_workflow.py`
- `tests/test_commit.py`
- `tests/test_smart_commit.py`
- `tests/test_python_feature.py`
- `tests/test_cli.py` (tests the old CLI structure)

### Modules that may have dead code after deletion

- `core/branch.py` — branch management utilities used by workflows
- `core/iteration.py` — iteration loop used by bugfix/feature
- `core/state.py` — checkpoint/resume used by workflows

These should be deleted if nothing else imports them after the workflows are removed.

## What Gets Modified

- `cli.py` — rewritten: single `audit` command, argparse, parallel dispatch
- `agents/__init__.py` — add `AUDITORS` dict and `get_auditor()` function; remove exports of workflow-only agents if unused
- `__main__.py` — no changes needed (already calls `cli.main`)

## What Stays Unchanged

- `core/runner.py` — `run_agent()`, `InteractiveSession`, event processing
- `core/events.py` — all event types
- `core/types.py` — `AgentDefinition`, `RunResult`, `TokenUsage`
- `core/diff.py` — `snapshot()`, `generate_patch()`
- `core/discovery.py` — `discover_files()`
- `core/config.py` — `ProjectConfig`
- `core/hooks.py` — hook building
- `core/sandbox.py` — sandbox restriction
- `display/` — all display modules
- `agents/` — all agent factory modules
- `prompts/` — all prompt constants
