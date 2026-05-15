# File Auditor Gold Standard Design

Date: 2026-05-13
Status: approved

## Goal

Refine `python_file_auditor.py` into the gold-standard agent pattern that other agents will eventually adopt. Two changes: simplify the factory interface and restructure the system prompt via section compose helpers.

## Context

The file auditor is already the simplest agent in the codebase — no structured output, just reads a file and fixes it. But its factory takes both `file` and `content`, pushing file I/O onto the caller. And the system prompt is built as one large f-string, making it hard to scan the agent definition at a glance.

This is the first step in a broader effort to standardize all agents around this pattern: factory takes minimal input, reads what it needs internally, agent does the work directly, runner captures a `.patch` at the end.

## Changes

### 1. Factory interface simplification

**Before:**
```python
def make_python_file_auditor(*, file: str, content: str) -> AgentDefinition:
```

**After:**
```python
def make_python_file_auditor(file: str) -> AgentDefinition:
```

- Drop `content` parameter; factory reads the file internally via `Path(file).read_text()`
- Drop keyword-only (`*`) since there's only one parameter
- Content still gets injected into the system prompt for prompt caching benefits

### 2. System prompt via section compose helpers

Replace the single large f-string with private helper functions that each return a prompt section string:

- `_role() -> str` — role description
- `_source_file(file: str, content: str) -> str` — file path + fenced code block
- `_method(file: str) -> str` — numbered audit steps
- `_rules(file: str) -> str` — guardrails

A `_build_system_prompt(file, content)` function composes these with the imported prompt constants and joins with `"\n\n"`.

### 3. Caller update

`workflows/audit.py` changes from:
```python
content = Path(file_path).read_text()
agent = make_python_file_auditor(file=file_path, content=content)
```
to:
```python
agent = make_python_file_auditor(file_path)
```

### 4. Test update

`tests/test_python_file_auditor.py` updated to match the new single-arg factory interface.

## What stays the same

- Agent name format: `python_file_auditor:{filename}`
- Model: `sonnet`
- Tools: `["Edit"]` (Read is unnecessary since content is in the prompt)
- No `output_schema`
- No hooks
- Prompt content (role, method, rules, checklists) — same words, just reorganized
- Runner's automatic `.patch` capture via `generate_patch`

## Files to modify

1. `codemonkeys/agents/python_file_auditor.py` — factory + prompt builder
2. `codemonkeys/workflows/audit.py` — caller simplification
3. `tests/test_python_file_auditor.py` — match new interface
