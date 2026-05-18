# Codemonkeys

Code review and development toolkit powered by Claude Code skills and AGENT.md definitions. Engineering judgment, workflow, and standards encoded as agent pipelines — all running natively within Claude Code (no external SDK or CLI).

## Architecture

Skills (`.claude/skills/`) orchestrate multi-phase workflows. Focused subagents are dispatched via the Claude Code Agent tool using `subagent_type` to enforce tool restrictions and isolation from AGENT.md frontmatter.

```
Skill → picks subagent_type by context → spawns Agent tool → merges results
```

### Agent Definitions (`.claude/agents/`)

Each AGENT.md has YAML frontmatter (`tools`, `model`, `isolation`) enforced by Claude Code, plus a markdown body with role, rules, and checklists:

**Reviewer** (read-only, `tools: Read`):
- **`codemonkeys-code-reviewer`** — single reviewer for all supported languages. Contains language-specific security, resilience, performance, accessibility, and architecture checklists; applies only the checklists matching the target file's extension.

Contains code quality, design, and test quality checklists inline. Reads language guidelines from `.claude/shared/` on demand (only the file matching the target language). Accepts context files (imports, callers) to improve accuracy but only reports findings on the target file. Output uses a strict structured format for reliable parsing.

**Editor** (`tools: Read, Edit, Write`, `isolation: worktree`):
- **`codemonkeys-code-editor`** — applies edits to files based on instructions or findings. Supports all languages. Reads language guidelines from `.claude/shared/` on demand.

**Researcher** (`tools: WebFetch, WebSearch, Write`, `model: opus`):
- **`codemonkeys-researcher`** — autonomous web research, produces SKILL.md or markdown reports.

### Skills (`.claude/skills/`)

**Workflow skills (user-invocable):**
- **`codemonkeys-code-review`** — 8-phase review pipeline: gather context files, dispatch reviewers in parallel, deduplicate findings, visualize, dispatch editors for selected fixes, verify with tests, re-review edited files
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
- **Worktree isolation:** Editor agents run in git worktrees. Changes are verified via `git diff` before merging back. Reviewers are read-only (`tools: Read`) and run without worktree isolation for efficiency.
- **Post-edit verification:** Skills run tests after merging editor changes; offer to revert on failure.
- **Re-review pass:** After fixes are applied, edited files are re-reviewed to catch issues introduced by the editor.

## Supported Languages

`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`
