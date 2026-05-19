# Codemonkeys

Code review and development toolkit powered by Claude Code skills and AGENT.md definitions. Engineering judgment, workflow, and standards encoded as agent pipelines — all running natively within Claude Code (no external SDK or CLI).

## Architecture

Skills (`.claude/skills/`) orchestrate multi-phase workflows. Focused subagents are dispatched via the Claude Code Agent tool using `subagent_type` to enforce tool restrictions and isolation from AGENT.md frontmatter.

```
Skill → picks subagent_type by context → spawns Agent tool → merges results
```

### Agent Definitions (`.claude/agents/`)

Each AGENT.md has YAML frontmatter (`tools`, `model`, `isolation`) enforced by Claude Code, plus a markdown body with role, rules, and checklists:

**Reviewers** (read-only, `tools: Read`):
- **`codemonkeys-code-reviewer`** — single reviewer for all supported languages. Contains language-specific security, resilience, performance, accessibility, and architecture checklists; applies only the checklists matching the target file's extension. Contains code quality, design, and test quality checklists inline. Reads language guidelines from `.claude/shared/` on demand (only the file matching the target language). Accepts context files (imports, callers) to improve accuracy but only reports findings on the target file. Output uses a strict structured format for reliable parsing.
- **`codemonkeys-test-reviewer`** — dedicated test quality reviewer. Analyzes test files alongside their source code to detect over-mocking, weak assertions, coverage gaps, and test design issues. Checklists: mock abuse (mocking the subject, mock masking, mock drift), assertion quality (missing, tautological, weak, implementation-coupled), coverage gaps (branches, boundaries, public API), test design (structure, setup, type mismatch). Reads language guidelines from `.claude/shared/` on demand.

**Editor** (`tools: Read, Edit, Write`, `isolation: worktree`):
- **`codemonkeys-code-editor`** — applies edits to files based on instructions or findings. Supports all languages. Reads language guidelines from `.claude/shared/` on demand.

**Researcher** (`tools: WebFetch, WebSearch, Write`, `model: opus`):
- **`codemonkeys-researcher`** — autonomous web research, produces SKILL.md or markdown reports.

### Skills (`.claude/skills/`)

**Workflow skills (user-invocable):**
- **`codemonkeys-code-review`** — 7-phase review pipeline: gather context files, batch reviewers by language, deduplicate findings, visualize, dispatch editors for selected fixes (with self-validation), verify with tests
- **`codemonkeys-test-quality`** — 5-phase test quality pipeline: discover test files and map to source, dispatch test-reviewer agents in parallel (test + source as context), deduplicate findings, visualize, dispatch editors for selected fixes
- **`codemonkeys-bugfix`** — investigation → diagnosis → sandboxed fix
- **`codemonkeys-feature`** — design spec → implementation plan → sandboxed execution → compliance review
- **`codemonkeys-research`** — autonomous web research with structured output
- **`codemonkeys-visualize`** — generates single-file HTML+JS pages for displaying findings, comparisons, architecture diagrams
- **`codemonkeys-smart-commit`** — structured commit messages with branch management

### Shared Reference Files (`.claude/shared/`)

Read-only reference documents consumed by agents on demand — not skills or workflows:
- **`python-guidelines.md`** — Python language guidelines
- **`js-guidelines.md`** — JavaScript/TypeScript language guidelines
- **`css-guidelines.md`** — CSS language guidelines
- **`html-guidelines.md`** — HTML language guidelines

### Safety Model

- **Tool restrictions:** AGENT.md frontmatter `tools` field enforced by Claude Code — reviewers can only Read, editors can only Read/Edit/Write, researcher can only search web and Write.
- **Post-edit verification:** Skills verify editor changes via `git diff` and run tests; offer to revert on failure.
- **Editor self-validation:** Each editor agent re-reads modified files after editing and checks for regressions in the flagged issue categories before returning.

## Supported Languages

`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`
