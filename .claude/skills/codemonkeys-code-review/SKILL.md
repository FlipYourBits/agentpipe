---
name: codemonkeys-code-review
description: Use when the user wants to review code for issues, audit files, or run a code review — spawns read-only reviewer agents per file, presents findings in an HTML page, and dispatches sandboxed editor agents to fix what the user selects
---

Run the codemonkeys review pipeline. Review files for issues, present findings visually, and edit what the user selects.

**Phase markers:** Announce each phase to the user as you enter it: `[1/5] Targets`, `[2/5] Review`, `[3/5] Findings`, `[4/5] Fixes`, `[5/5] Verify`.

## Red Flags — Stop and Follow the Process

| If you're thinking... | The reality is... |
|---|---|
| "I'll just fix the issues myself without running the review" | The review pipeline catches things you won't. Run it. |
| "These changes are too small to review" | Small changes cause production incidents. Review everything. |
| "I already know what's wrong, skip to editing" | Run the review — you'll find things you didn't expect. |
| "Let me review the code by reading it instead" | You're not the reviewer. The agents have structured checklists you don't. |

## Process

### 1. Determine targets

Figure out what to review. Ask the user if not obvious from context:

- **Branch diff (default):** files changed on the current branch vs main — `--diff`
- **Specific patterns:** e.g. `codemonkeys/agents/*.py`, `src/**/*.py`
- **Both:** diff-scoped with pattern filtering

If the user says "audit my changes" or "review what I changed", use `--diff`.

### 2. Run the review

```bash
codemonkeys review --diff
codemonkeys review '**/*.py'
codemonkeys review --diff '*.py'
```

Show the exact command before running it. The agents are read-only (Sonnet) — they report findings but don't edit anything.

The CLI auto-suppresses verbose output when not a TTY. Results are written to `.codemonkeys/<timestamp>_review-results.json` (the exact path is printed in the CLI output).

### 3. Read results and generate visual companion

After the command completes:

1. Read the review results JSON file (path printed by the CLI)
2. Invoke the `codemonkeys-visualize` skill to generate an HTML page with all findings:
   - Group findings by file
   - Color-code by severity (high=red, medium=yellow, low=blue)
   - Show category, line number, title, description, suggestion for each
   - Make findings selectable/checkable so the user can reference them by number
3. Open the HTML page in the browser

### 4. Ask what to fix

Tell the user what was found and ask what to fix. Examples:
- "Fix all high severity findings"
- "Fix findings 1, 3, 5 in runner.py"
- "Fix everything in cli.py"
- "Skip all"

### 5. Dispatch editors

For each file with selected findings, run:

```bash
codemonkeys edit <file_path> --findings 1,3,5
```

This dispatches a `code_editor:fix` agent scoped to `Read(file)` + `Edit(file)`. One agent per file, batching all selected findings.

### 6. Verify

After all edits are applied, run the test suite to catch broken imports, renames that rippled across files, or regressions:

```bash
uv run pytest
```

- If tests **pass**: move on to showing results.
- If tests **fail**: show the failures to the user and offer to fix them. Re-dispatch `codemonkeys edit` on the failing file(s) with the test error as the task, or fix directly if the issue is simple (e.g. a missed rename).

### 7. Show results

After edits are applied and tests pass:
- `git diff` to review changes
- `git checkout -- <path>` to revert a specific file
- `codemonkeys review-logs <log_dir>` to review agent behavior

## Supported Extensions

The `REVIEWERS` registry in `codemonkeys/agents/__init__.py` controls which
file extensions can be reviewed. Currently registered: `.py`. Files with
unregistered extensions are skipped with a warning.

### 8. Commit

When the user wants to commit the changes, invoke the `codemonkeys-smart-commit` skill. Do not use the built-in git commit workflow.

## Rules

- Always show the exact command before running it.
- The review phase is read-only — no files are modified until the user selects findings to fix.
- Don't suggest `--max-parallel` unless the user has a reason to change it.
