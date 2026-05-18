# Codemonkeys

Code review and development toolkit powered by Claude Code skills and agent definitions. Engineering judgment, workflow, and standards encoded as agent pipelines — all running natively within Claude Code.

## How It Works

Skills orchestrate multi-phase workflows by dispatching focused subagents via the Claude Code `Agent` tool. Each agent has strict tool restrictions and git worktree isolation defined in its AGENT.md frontmatter.

```
User invokes skill → Skill reads context → Dispatches agents → Merges results
```

## Skills

Skills are user-invocable workflows that coordinate one or more agents.

### `/codemonkeys-code-review`

Multi-file code review pipeline. Gathers context files (imports, callers) per target, dispatches reviewer agents in parallel, deduplicates findings, renders them in an interactive HTML page, dispatches editor agents for selected fixes, and re-reviews edited files to catch introduced issues.

**Phases:** Targets → Context & Review → Findings → Visualize → Fixes → Verify → Re-review → Done

**Supported:** `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html`

---

### `/codemonkeys-bugfix`

Bug investigation and fix pipeline. Traces root cause by reading stack traces and following call chains, writes a structured diagnosis, then dispatches a sandboxed editor agent to apply the fix.

**Phases:** Branch setup → Investigation → Diagnosis → Fix

**Output:** `.codemonkeys/YYYYMMDD-HHMMSS_bug-diagnosis.md`

---

### `/codemonkeys-feature`

Full feature lifecycle from design through implementation. Interactive brainstorming, design spec, implementation plan with TDD steps, sandboxed agent execution, and post-implementation spec compliance review.

**Phases:** Branch setup → Brainstorm → Plan → Implement → Compliance review

**Output:** Design spec + feature plan in `.codemonkeys/`

---

### `/codemonkeys-research`

Dispatches an autonomous research agent that searches the web, reads sources, follows reference chains, and produces structured output.

**Output formats:**
- Claude Code skill (`.claude/skills/<topic>/SKILL.md`)
- Markdown report (`.codemonkeys/research/`)
- HTML visualization (markdown + browser render)

---

### `/codemonkeys-visualize`

Generates single-file HTML+JS pages for displaying architecture diagrams, data flows, side-by-side comparisons, UI mockups, audit findings, and more. Opens in the browser for interactive review.

**Output:** `.codemonkeys/visuals/YYYYMMDD-HHMMSS_<name>.html`

**Visualization types:** Architecture diagram, data flow, side-by-side comparison, UI mockup, component map, timeline, tree hierarchy, table view, diff view, metrics dashboard, code display

---

### `/codemonkeys-smart-commit`

Structured commit workflow with branch hygiene. Detects if you're on main and offers to create a feature branch, updates docs (README, CHANGELOG, CLAUDE.md) via a sandboxed editor when changes are meaningful, generates a structured commit message, and offers to push.

---

### Shared Reference Files

Read-only reference documents in `.claude/shared/`, read by agents on demand (only the files matching the target language).

| File | Purpose |
|------|---------|
| `python-guidelines.md` | Python language guidelines |
| `js-guidelines.md` | JavaScript/TypeScript language guidelines |
| `css-guidelines.md` | CSS language guidelines |
| `html-guidelines.md` | HTML language guidelines |

## Agents

Agents are specialized subagents with strict tool and isolation constraints defined in AGENT.md frontmatter.

### Reviewer

Read-only agent that analyzes code and returns structured findings. Contains code quality, design, test quality, and language-specific security/resilience/performance checklists inline; applies only the checklists matching the target file's extension. Reads language guidelines from `.claude/shared/` on demand. Accepts context files (imports, callers) to improve accuracy but only reports findings on the target file.

| Agent | Languages | Tools | Model | Isolation |
|-------|-----------|-------|-------|-----------|
| `codemonkeys-code-reviewer` | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.html` | Read | Opus | — |

### Editor

| Agent | Purpose | Tools | Model | Isolation |
|-------|---------|-------|-------|-----------|
| `codemonkeys-code-editor` | Applies targeted edits based on task instructions | Read, Edit, Write | Sonnet | — |

Supports all languages. Reads language guidelines from `.claude/shared/` on demand. Never runs commands or modifies git state.

### Researcher

| Agent | Purpose | Tools | Model | Isolation |
|-------|---------|-------|-------|-----------|
| `codemonkeys-researcher` | Autonomous web research | WebFetch, WebSearch, Write | Opus | — |

Searches the web, reads documents, follows reference chains, and writes structured reports.

## Safety Model

- **Tool restrictions:** Agent frontmatter `tools` field is enforced by Claude Code — reviewers can only Read, editors can only Read/Edit/Write, researcher can only search and Write.
- **Post-edit verification:** Skills verify editor changes via `git diff` and run tests; offer to revert on failure.
- **Re-review pass:** After fixes are applied, edited files are re-reviewed to catch issues introduced by the editor.
- **No auto-commit/push:** All commits and pushes require explicit user approval.

## Project Structure

```
.claude/
├── agents/
│   ├── codemonkeys-code-reviewer/AGENT.md
│   ├── codemonkeys-code-editor/AGENT.md
│   └── codemonkeys-researcher/AGENT.md
├── shared/
│   ├── python-guidelines.md
│   ├── js-guidelines.md
│   ├── css-guidelines.md
│   └── html-guidelines.md
├── skills/
│   ├── codemonkeys-code-review/SKILL.md
│   ├── codemonkeys-bugfix/SKILL.md
│   ├── codemonkeys-feature/SKILL.md
│   ├── codemonkeys-research/SKILL.md
│   ├── codemonkeys-visualize/SKILL.md
│   └── codemonkeys-smart-commit/SKILL.md
└── settings.json
```

## Installation

Install codemonkeys into any project that uses Claude Code.

**Linux / macOS:**

```bash
curl -sL https://raw.githubusercontent.com/FlipYourBits/codemonkeys/main/install.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/FlipYourBits/codemonkeys.git
cd your-project
../codemonkeys/install.sh
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/FlipYourBits/codemonkeys.git
cd your-project
..\codemonkeys\install.ps1
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--branch` / `-Branch` | Git branch to install from | `main` |
| `--dir` / `-Dir` | Target project directory | Current directory |

Re-run anytime to update to the latest version.

## Usage

All skills are invoked as slash commands within Claude Code:

```
/codemonkeys-code-review          # review changed files
/codemonkeys-bugfix               # investigate and fix a bug
/codemonkeys-feature              # design and build a feature
/codemonkeys-research             # research a topic
/codemonkeys-visualize            # generate a visualization
/codemonkeys-smart-commit         # commit with branch hygiene
```
