# Codemonkeys

Code review and development toolkit powered by Claude Code skills and AGENT.md definitions. Engineering judgment, workflow, and standards encoded as agent pipelines — all running natively within Claude Code (no external SDK or CLI).

## Architecture

Skills (`.claude/skills/`) orchestrate multi-phase workflows. Focused subagents are dispatched via the Claude Code Agent tool using `subagent_type` to enforce tool restrictions and isolation from AGENT.md frontmatter.

```
Skill → picks subagent_type by context → spawns Agent tool → merges results
```

### Agent Definitions (`.claude/agents/`)

Each AGENT.md has YAML frontmatter (`tools`, `model`, `isolation`) enforced by Claude Code, plus a markdown body with role, rules, and checklists:

**Reviewers** (read-only, `tools: Read`, `isolation: worktree`):
- **`codemonkeys-python-reviewer`** — Python security, resilience, performance checklists
- **`codemonkeys-js-reviewer`** — JS/TS security (XSS, prototype pollution), resilience, performance checklists
- **`codemonkeys-css-reviewer`** — CSS specificity, architecture, accessibility checklists
- **`codemonkeys-html-reviewer`** — HTML security (XSS, CSP), accessibility, semantic structure checklists

All reviewers preload shared code quality and design checklists via `skills: [codemonkeys-review-checklists]`.

**Editor** (`tools: Read, Edit, Write`, `isolation: worktree`):
- **`codemonkeys-code-editor`** — applies edits to files based on instructions or findings. Supports all languages.

**Researcher** (`tools: WebFetch, WebSearch, Write`, `model: opus`):
- **`codemonkeys-researcher`** — autonomous web research, produces SKILL.md or markdown reports.

### Language Guidelines (`.claude/agents/codemonkeys-guidelines/`)

Shared language-specific guidelines loaded by skills at dispatch time for both reviewer and editor agents: `python.md`, `javascript.md`, `css.md`, `html.md`.

### Skills (`.claude/skills/`)

- **`codemonkeys-code-review`** — multi-file review pipeline: dispatch per-language reviewer agents in parallel, visualize findings, dispatch editors for selected fixes
- **`codemonkeys-bugfix`** — investigation → diagnosis → sandboxed fix
- **`codemonkeys-feature`** — design spec → implementation plan → sandboxed execution → compliance review
- **`codemonkeys-research`** — autonomous web research with structured output
- **`codemonkeys-visualize`** — generates single-file HTML+JS pages for displaying findings, comparisons, architecture diagrams
- **`codemonkeys-smart-commit`** — structured commit messages with branch management
- **`codemonkeys-review-checklists`** — shared code quality, design, and test quality checklists (not user-invocable, preloaded by reviewer agents)

### Safety Model

- **Tool restrictions:** AGENT.md frontmatter `tools` field enforced by Claude Code — reviewers can only Read, editors can only Read/Edit/Write, researcher can only search web and Write.
- **Worktree isolation:** Reviewer and editor agents run in git worktrees. Changes are verified via `git diff` before merging back.
- **Post-edit verification:** Skills run tests after merging editor changes; offer to revert on failure.

## Supported Languages

`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`
