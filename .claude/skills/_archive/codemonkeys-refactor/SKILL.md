---
name: codemonkeys-refactor
description: Use when the user wants to refactor code, improve architecture, clean up design issues, or fix cross-file dependencies — runs a read-only architecture analysis agent, presents findings, and dispatches sandboxed editor agents to fix what the user selects
---

Analyze the codebase for architectural issues and refactor what the user selects.

## Branch Setup

Before starting, check the current branch with `git branch --show-current`.

- **On `main` or `master`:** Suggest creating a refactor branch. Generate a name from the context: `refactor/<short-slug>`. Ask: "You're on main. Want me to create `refactor/<slug>` for this work?"
- **On matching prefix** (`refactor/`, `perf/`, `style/`, `chore/`, `build/`, or `ci/`): Proceed silently.
- **On wrong prefix** (anything else): Warn the user: "You're on `<branch>` — that doesn't look like a refactor branch. Want me to create `refactor/<slug>` instead, or continue here?"

If creating a branch: `git checkout -b refactor/<slug>`

## Process

### 1. Run the architecture analysis

```bash
codemonkeys architecture
```

Run via Bash. This spawns a single read-only Agent SDK agent with its own sandbox and permissions. It reads across the project and produces structured findings in `.codemonkeys/architecture-findings.md`.

### 2. Interpret results

After the command completes:

- Read `.codemonkeys/architecture-findings.md`
- Summarize the findings — how many, severity, which areas of the codebase
- Highlight the most actionable ones

### 3. Ask what to fix

Present findings and ask the user what to address. Examples:
- "Fix all high severity findings"
- "Fix findings 1, 3, 5"
- "Fix everything related to circular imports"
- "Skip all"

### 4. Dispatch editors

For each selected finding, dispatch a sandboxed editor:

```bash
codemonkeys edit <file1> [file2 ...] \
  --task-type refactor \
  --task "<finding description + suggestion>"
```

Group findings by file when possible — one agent per file, batching related findings.

### 5. Show results

After edits are applied:
- `git diff` to review changes
- `git checkout -- <path>` to revert a specific file
- Offer to run tests: `pytest tests/ -x -q`

## Rules

- The analysis phase is read-only — no files are modified until the user selects findings to fix.
- Read the actual findings file to give a useful summary — don't just echo the CLI output.
- No arguments to collect for the analysis — just run it.
