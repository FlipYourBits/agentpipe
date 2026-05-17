---
name: codemonkeys-code-review
description: Use when the user wants to review code for issues, audit files, or run a code review — spawns read-only reviewer agents per file, presents findings in an HTML page, and dispatches sandboxed editor agents to fix what the user selects
---

Run the codemonkeys review pipeline. Review files for issues, present findings visually, and edit what the user selects.

**Phase markers:** Announce each phase to the user as you enter it: `[1/7] Targets`, `[2/7] Review`, `[3/7] Findings`, `[4/7] Visualize`, `[5/7] Fixes`, `[6/7] Verify`, `[7/7] Done`.

## Red Flags — Stop and Follow the Process

| If you're thinking... | The reality is... |
|---|---|
| "I'll just fix the issues myself without running the review" | The review pipeline catches things you won't. Run it. |
| "These changes are too small to review" | Small changes cause production incidents. Review everything. |
| "I already know what's wrong, skip to editing" | Run the review — you'll find things you didn't expect. |
| "Let me review the code by reading it instead" | You're not the reviewer. The agents have structured checklists you don't. |

## Supported Extensions

The reviewer supports: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`. Files with other extensions are skipped with a warning.

## Reviewer Agent Selection

Each file type is reviewed by a language-specific reviewer agent. Pick the right `subagent_type` by extension:

| Extension | `subagent_type` |
|-----------|----------------|
| `.py` | `codemonkeys-python-reviewer` |
| `.js`, `.jsx`, `.ts`, `.tsx` | `codemonkeys-js-reviewer` |
| `.css` | `codemonkeys-css-reviewer` |
| `.html` | `codemonkeys-html-reviewer` |

Each reviewer agent has language-specific security, resilience, and performance checklists baked in, plus shared code quality and design checklists preloaded via the `codemonkeys-review-checklists` skill.

## Process

### [1/7] Targets

Figure out what to review. Ask the user if not obvious from context:

- **Branch diff (default):** files changed on the current branch vs main — run `git diff main...HEAD --name-only`
- **Specific patterns:** e.g. `codemonkeys/agents/*.py`, `src/**/*.py` — use `find` or `git ls-files` with pattern matching
- **Both:** diff-scoped with pattern filtering

If the user says "audit my changes" or "review what I changed", use branch diff.

Filter to supported extensions only. Warn about skipped files.

### [2/7] Review

For each target file, dispatch the appropriate language-specific reviewer agent:

1. Read the appropriate language guidelines from `.claude/agents/codemonkeys-guidelines/` based on file extension:
   - `.py` → read `python.md`
   - `.js`, `.jsx`, `.ts`, `.tsx` → read `javascript.md`
   - `.html` → read `html.md` + `javascript.md` + `css.md`
   - `.css` → read `css.md`
2. For each file, spawn an Agent tool call with:
   - `subagent_type`: select from the reviewer agent selection table above based on file extension
   - `prompt`: guidelines content + `"\n\n## Task\n\nReview the file: <file_path>"`

Spawn **all reviewer agents in parallel** (multiple Agent tool calls in a single message). Each agent will read the file and return structured markdown findings. Group files by extension so you only read each guidelines file once.

Tell the user how many files are being reviewed before dispatching.

### [3/7] Findings

After all reviewer agents return:

1. Collect findings from each agent's text output
2. Parse the structured markdown (each finding has File, Line, Severity, Category, Title, Description, Suggestion)
3. Count total findings by severity
4. Report summary to user: "Found X findings across Y files (Z high, W medium, V low)"

If no findings across all files, announce "No issues found" and stop.

### [4/7] Visualize

Invoke the `codemonkeys-visualize` skill to generate an HTML page showing all findings:
- Group findings by file
- Color-code by severity (high=red, medium=yellow, low=blue)
- Show category, line number, title, description, suggestion for each
- Number each finding so the user can reference them

Open the HTML page in the browser.

### [5/7] Fixes

Ask the user what to fix. Examples of valid responses:
- "Fix all high severity findings"
- "Fix findings 1, 3, 5"
- "Fix everything in runner.py"
- "Skip all"

If the user wants to skip, go to [7/7].

For each file with selected findings:

1. Read the appropriate language guidelines from `.claude/agents/codemonkeys-guidelines/` based on file extension
2. Spawn an Agent tool call with:
   - `subagent_type: "codemonkeys-code-editor"` (enforces file-only tools and worktree isolation from AGENT.md frontmatter)
   - `prompt`: guidelines content + `"\n\n## Task\n\nFix the following issues in <file_path>:\n\n<selected findings for this file>"`

Spawn one editor agent per file. If multiple files need fixes, dispatch them in parallel.

After each editor agent completes:
- The agent made changes in a worktree — the result will include the worktree branch
- Merge the changes back: `git checkout <worktree-branch> -- <file_path>`

### [6/7] Verify

After all edits are merged back, run the test suite:

```bash
uv run pytest -x -q 2>/dev/null || npm test 2>/dev/null || echo "No test runner found"
```

- If tests **pass**: proceed to done.
- If tests **fail**: show the failures to the user and offer to fix them. Dispatch another editor agent on the failing file(s) with the test error as the task.

### [7/7] Done

Show results:
- `git diff` to review all changes
- Offer: `git checkout -- <path>` to revert a specific file
- When the user wants to commit, invoke the `codemonkeys-smart-commit` skill.

## Rules

- The review phase is read-only — no files are modified until the user selects findings to fix.
- Always tell the user what you're about to do before dispatching agents.
- Don't suggest fixing everything unless the user asks — let them choose.
- If a reviewer agent returns garbled output, skip that file's findings and warn the user.
