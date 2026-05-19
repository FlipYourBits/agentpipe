---
name: codemonkeys-code-review
description: Use when the user wants to review code for issues, audit files, or run a code review — spawns read-only reviewer agents per file, presents findings in an HTML page, and dispatches sandboxed editor agents to fix what the user selects
---

Run the codemonkeys review pipeline. Review files for issues, present findings visually, and edit what the user selects.

**Phase markers:** Announce each phase to the user as you enter it: `[1/7] Targets`, `[2/7] Context & Review`, `[3/7] Findings`, `[4/7] Visualize`, `[5/7] Fixes`, `[6/7] Verify`, `[7/7] Done`.

## Red Flags — Stop and Follow the Process

| If you're thinking... | The reality is... |
|---|---|
| "I'll just fix the issues myself without running the review" | The review pipeline catches things you won't. Run it. |
| "These changes are too small to review" | Small changes cause production incidents. Review everything. |
| "I already know what's wrong, skip to editing" | Run the review — you'll find things you didn't expect. |
| "Let me review the code by reading it instead" | You're not the reviewer. The agents have structured checklists you don't. |

## Supported Extensions

The reviewer supports: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`. Files with other extensions are skipped with a warning.

## Reviewer Agent

All files are reviewed by the same agent: `subagent_type: codemonkeys-code-reviewer`. It reads language-specific guidelines from `.claude/shared/` on demand and applies only the checklists matching the target file's language.

## Reference Files

Shared checklists and language guidelines live in `.claude/shared/`. Include the relevant paths in the agent prompt so it reads only what it needs.

| Extension | Reference file to include |
|-----------|--------------------------|
| `.py` | `.claude/shared/python-guidelines.md` |
| `.js`, `.jsx`, `.ts`, `.tsx` | `.claude/shared/js-guidelines.md` |
| `.css` | `.claude/shared/css-guidelines.md` |
| `.html` | `.claude/shared/html-guidelines.md` |

## Process

### [1/7] Targets

Figure out what to review. Ask the user if not obvious from context:

- **Branch diff (default):** files changed on the current branch vs main — run `git diff main...HEAD --name-only`
- **Specific patterns:** e.g. `codemonkeys/agents/*.py`, `src/**/*.py` — use `find` or `git ls-files` with pattern matching
- **Both:** diff-scoped with pattern filtering

If the user says "audit my changes" or "review what I changed", use branch diff.

Filter to supported extensions only. Warn about skipped files.

### [2/7] Context & Review

#### Batch large reviews

If there are more than 15 target files, batch them in groups of 15. Process each batch fully through [3/7] Findings before starting the next batch. Merge findings across all batches before proceeding to [4/7] Visualize. Tell the user: "Reviewing in N batches of up to 15 files each."

#### Gather context files

For each target file, identify up to 5 context files that will help the reviewer understand imports, types, and callers. Context files are read-only references — the reviewer reports findings only on the target file.

**Run all context-gathering commands in parallel** — one batch of Bash calls per target file. Each file's imports and callers are independent, so dispatch them all simultaneously.

**For `.py` files:**
```bash
# Direct imports — extract imported module paths from the target file
grep -E "^(from|import) " <file> | sed 's/from \([^ ]*\).*/\1/' | sed 's/import \([^ ]*\).*/\1/' | head -5
# Callers — files that import the target module
grep -rl "from $(basename <file> .py)\|import $(basename <file> .py)" --include="*.py" . | head -5
```

**For `.js`/`.ts`/`.jsx`/`.tsx` files:**
```bash
# Direct imports — extract relative import paths from the target file
grep -oE "(from|require\()\s*['\"]\.\.?/[^'\"]+['\"]" <file> | head -5
# Callers — files that import the target module
grep -rl "from.*$(basename <file> | sed 's/\.[^.]*$//')\|require.*$(basename <file> | sed 's/\.[^.]*$//')" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" . | head -5
```

**For `.css` files:**
```bash
# HTML files that link this stylesheet
grep -rl "$(basename <file>)" --include="*.html" . | head -5
```

**For `.html` files:**
```bash
# CSS and JS files referenced by this HTML file
grep -oE '(href|src)="[^"]*\.(css|js)"' <file> | sed 's/.*="//' | sed 's/"//' | head -5
```

Cap at 5 context files per target. If a context file is also a target file being reviewed, still include it — each reviewer runs independently.

#### Batch by language and dispatch reviewers

Group target files by language using the extension → reference file mapping. Within each language group, batch up to 5 files per reviewer agent. This reduces token overhead — each agent reads the language guidelines once for all files in its batch instead of once per file.

For each batch, merge the context files gathered for all target files in the batch, deduplicate, and cap at 8 context files per batch. Exclude files that are already target files in the same batch (the reviewer will read them anyway).

For each batch, spawn an Agent tool call with:
- `subagent_type`: `codemonkeys-code-reviewer`
- `prompt`:
  ```
  ## Task

  Review the following files:
  - <target_file_1>
  - <target_file_2>
  - <target_file_3>

  ## Reference Files

  Read before reviewing:
  - .claude/shared/<language>-guidelines.md

  ## Context Files

  The following files are available for you to read for context (imports, types, callers). Do not report findings on these files:
  - <context_file_1>
  - <context_file_2>
  ...
  ```

Use the Reference Files mapping above to pick the correct guideline file for the batch's language. If no context files were found, omit the Context Files section.

Spawn **all reviewer agents in parallel** (multiple Agent tool calls in a single message). Each agent reviews all files in its batch and returns structured markdown findings with the correct file path per finding.

Tell the user how many files are being reviewed across how many reviewer agents before dispatching.

### [3/7] Findings

After all reviewer agents return:

1. Collect findings from each agent's text output
2. Parse the structured markdown — each finding has a title in the heading (`### Finding: <title>`) and fields: File, Line, Severity, Category, Description, Suggestion
3. **Deduplicate:** If multiple reviewers flagged findings with the same title and description (or near-identical — same pattern, different files), collapse them into a single finding with a list of affected files. This is common when the same anti-pattern repeats across files (e.g., "bare except clause" flagged in 8 files).
4. Count total findings by severity (after deduplication)
5. Report summary to user: "Found X findings across Y files (Z high, W medium, V low). N duplicates collapsed."

If no findings across all files, announce "No issues found" and stop.

### [4/7] Visualize

Use the HTML template at `.claude/skills/codemonkeys-code-review/templates/findings.html`:

1. Read the template file.
2. Build a JSON array from the deduplicated findings. Each entry: `{ id, file, line, severity, category, title, description, suggestion }`. The `id` is the finding's sequential number.
3. In the template, replace `const findings = [];` (the line between the `FINDINGS_DATA` comments) with `const findings = <JSON array>;`.
4. Write the result to `.codemonkeys/visuals/YYYYMMDD-HHMMSS_code-review.html`. Create the directory if needed.
5. Open in browser:
   - Linux: `xdg-open <file>`
   - macOS: `open <file>`
   - Windows (Git Bash / WSL): `start <file>` or `wslview <file>`
   - Fallback: `uv run python -m webbrowser <file>`

Do **not** invoke the `codemonkeys-visualize` skill — the template is self-contained.

### [5/7] Fixes

Ask the user what to fix. Examples of valid responses:
- "Fix all high severity findings"
- "Fix findings 1, 3, 5"
- "Fix everything in runner.py"
- "Skip all"

If the user wants to skip, go to [7/7].

For each file with selected findings:

1. Spawn an Agent tool call with:
   - `subagent_type: "codemonkeys-code-editor"` (enforces file-only tools from AGENT.md frontmatter)
   - `prompt`: Include the matching guideline reference file path, then the task:
     ```
     ## Reference Files

     Read before editing:
     - .claude/shared/<language>-guidelines.md

     ## Task

     Fix the following issues in <file_path>:

     <selected findings for this file>
     ```

Use the Reference Files mapping to pick the correct guideline file for the target file's extension.

Spawn one editor agent per file. If multiple files need fixes, dispatch them in parallel.

Each editor agent self-validates after editing — it re-reads modified files and checks for regressions in the same issue categories. This replaces the separate re-review pass.

After each editor agent completes, verify the changes with `git diff`.

### [6/7] Verify

Run the test suite:

```bash
uv run pytest -x -q 2>&1 || npm test 2>&1 || echo "No test runner found"
```

- If tests **pass**: proceed to done.
- If tests **fail**: show the failures to the user and offer to fix them. Dispatch another editor agent on the failing file(s) with the test error as the task. After fixing, re-run tests before proceeding.

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
