---
name: codemonkeys-test-quality
description: Use when the user wants to check test quality, audit test files, or find over-mocking and weak tests — maps test files to source, dispatches test-reviewer agents in parallel, presents findings in an HTML page, and dispatches sandboxed editor agents to fix what the user selects
---

Run the codemonkeys test quality pipeline. Analyze test files alongside their source code to find over-mocking, weak assertions, coverage gaps, and test design issues.

**Phase markers:** Announce each phase to the user as you enter it: `[1/5] Discovery`, `[2/5] Analysis`, `[3/5] Findings`, `[4/5] Visualize`, `[5/5] Fix`.

## Red Flags — Stop and Follow the Process

| If you're thinking... | The reality is... |
|---|---|
| "I'll just read the tests myself and point out issues" | The test-reviewer agent has structured checklists and sees both test + source. Use it. |
| "These tests look fine at a glance" | Glance reviews miss over-mocking and coverage gaps. Run the pipeline. |
| "I'll skip source mapping — the tests are self-explanatory" | The whole point is comparing what source does vs what tests verify. Map them. |
| "Let me fix the tests without reviewing first" | Run the review — you'll find things you didn't expect. |

## Supported Extensions

The test reviewer supports: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`. Test files for `.css` and `.html` are not applicable.

## Reference Files

| Extension | Reference file to include |
|-----------|--------------------------|
| `.py` | `.claude/shared/python-guidelines.md` |
| `.js`, `.jsx`, `.ts`, `.tsx` | `.claude/shared/js-guidelines.md` |

## Process

### [1/5] Discovery

Figure out what test files to review. Ask the user if not obvious from context:

- **All tests (default):** find test files in the project
- **Specific patterns:** e.g. `tests/test_auth.py`, `tests/unit/`
- **Branch diff:** test files changed on current branch vs main — `git diff main...HEAD --name-only`

**Finding test files:**

For Python:
```bash
find . -name "test_*.py" -o -name "*_test.py" | grep -v __pycache__ | grep -v .venv | sort
```

For JS/TS:
```bash
find . -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.test.js" -o -name "*.test.jsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" -o -name "*.spec.js" -o -name "*.spec.jsx" | grep -v node_modules | sort
```

Filter to supported extensions only.

#### Source Mapping

For each test file, identify the source file(s) it tests using convention-based mapping:

**Python:**
1. `test_foo.py` → look for `foo.py` in the project (same directory, parent directory, or `src/`)
2. Parse imports: `from mypackage.foo import ...` → `mypackage/foo.py`
3. If multiple candidates, prefer the one that shares the most path segments with the test file

```bash
# Extract local imports from a test file
grep -E "^(from|import) " <test_file> | grep -v "pytest\|unittest\|mock\|fixture\|conftest" | head -10
```

**JS/TS:**
1. `foo.test.ts` → `foo.ts` (same directory or parent)
2. `__tests__/foo.test.ts` → `../foo.ts`
3. Parse imports: `import { ... } from '../foo'` → resolve relative path

```bash
# Extract local imports from a test file
grep -oE "(from|require\()\s*['\"]\.\.?/[^'\"]+['\"]" <test_file> | head -10
```

For each test file, find up to 3 source files. If no source file can be mapped, still review the test file (the reviewer can detect mock abuse and assertion issues without source context, though coverage gap detection will be limited). Warn the user about unmapped files.

**Run all source-mapping commands in parallel** — each test file's mapping is independent.

Report to the user: "Found N test files. Mapped M to source files. K unmapped."

### [2/5] Analysis

#### Batch and dispatch reviewers

Group test files by language using the extension → reference file mapping. Within each language group, batch up to 3 test files per reviewer agent (smaller batches than code review because each test file also brings source files as context).

For each batch, spawn an Agent tool call with:
- `subagent_type`: `codemonkeys-test-reviewer`
- `prompt`:
  ```
  ## Task

  Review the following test files for test quality issues:
  - <test_file_1>
  - <test_file_2>
  - <test_file_3>

  ## Source Files

  These are the source files being tested. Read them to understand what the tests should be verifying — branches, error paths, edge cases, public API. Do not report findings on source files:
  - <test_file_1> tests → <source_file_1a>, <source_file_1b>
  - <test_file_2> tests → <source_file_2a>
  - <test_file_3> tests → <source_file_3a>

  ## Reference Files

  Read before reviewing:
  - .claude/shared/<language>-guidelines.md
  ```

If a test file has no mapped source files, omit it from the Source Files section and note: "No source mapping for <test_file> — review for mock abuse and assertion quality only."

Spawn **all reviewer agents in parallel** (multiple Agent tool calls in a single message).

Tell the user how many test files are being reviewed across how many reviewer agents before dispatching.

### [3/5] Findings

After all reviewer agents return:

1. Collect findings from each agent's text output
2. Parse the structured markdown — each finding has a title in the heading (`### Finding: <title>`) and fields: File, Line, Severity, Category, Description, Suggestion
3. **Deduplicate:** If multiple reviewers flagged findings with the same title and description (or near-identical — same pattern, different test files), collapse them into a single finding with a list of affected files. Common for repeated patterns like "mock.patch used without verifying call args" across test files.
4. Count total findings by severity and category (after deduplication)
5. Report summary to user: "Found X findings across Y test files (Z high, W medium, V low). N duplicates collapsed."

If no findings across all files, announce "No issues found — tests look solid" and stop.

### [4/5] Visualize

Use the HTML template at `.claude/skills/codemonkeys-test-quality/templates/findings.html`:

1. Read the template file.
2. Build a JSON array from the deduplicated findings. Each entry: `{ id, file, line, severity, category, title, description, suggestion }`. The `id` is the finding's sequential number.
3. In the template, replace `const findings = [];` (the line between the `FINDINGS_DATA` comments) with `const findings = <JSON array>;`.
4. Write the result to `.codemonkeys/visuals/YYYYMMDD-HHMMSS_test-quality.html`. Create the directory if needed.
5. Open in browser:
   - Linux: `xdg-open <file>`
   - macOS: `open <file>`
   - Windows (Git Bash / WSL): `start <file>` or `wslview <file>`
   - Fallback: `uv run python -m webbrowser <file>`

Do **not** invoke the `codemonkeys-visualize` skill — the template is self-contained.

### [5/5] Fix

Ask the user what to fix. Examples of valid responses:
- "Fix all high severity findings"
- "Fix findings 1, 3, 5"
- "Fix everything in test_auth.py"
- "Skip all"

If the user wants to skip, announce done and stop.

For each test file with selected findings:

1. Spawn an Agent tool call with:
   - `subagent_type: "codemonkeys-code-editor"`
   - `prompt`: Include the matching guideline reference file path, source file paths for context, then the task:
     ```
     ## Reference Files

     Read before editing:
     - .claude/shared/<language>-guidelines.md

     ## Source Files (read-only context)

     Read these to understand what the tests should verify:
     - <source_file_1>
     - <source_file_2>

     ## Task

     Fix the following test quality issues in <test_file>:

     <selected findings for this test file>
     ```

Spawn one editor agent per test file. If multiple files need fixes, dispatch them in parallel.

After each editor agent completes, verify the changes with `git diff`.

Run the test suite to confirm the improved tests still pass:

```bash
uv run pytest -x -q 2>&1 || npm test 2>&1 || echo "No test runner found"
```

- If tests **pass**: proceed to done.
- If tests **fail**: show the failures to the user and offer to fix them. Dispatch another editor agent on the failing file(s) with the test error as the task.

Show results:
- `git diff` to review all changes
- Offer: `git checkout -- <path>` to revert a specific file
- When the user wants to commit, invoke the `codemonkeys-smart-commit` skill.

## Rules

- The review phase is read-only — no files are modified until the user selects findings to fix.
- Always tell the user what you're about to do before dispatching agents.
- Don't suggest fixing everything unless the user asks — let them choose.
- If a reviewer agent returns garbled output, skip that file's findings and warn the user.
- Source files are never modified — only test files are edited.
