---
name: codemonkeys-smart-commit
description: Use when the user wants to commit changes, save work, or is done with a task — handles branch detection, offers to move changes off main onto a named feature branch, updates docs (README, CHANGELOG, CLAUDE.md) via a sandboxed editor agent when changes are meaningful, and generates a structured commit message
---

Commit the user's work. Handle branch hygiene, doc updates, and commit message generation.

## Process

### 1. Assess changes

Run these in parallel:

```bash
git status
git diff
git diff --cached
git log --oneline -5
git branch --show-current
```

If there are no uncommitted or staged changes, tell the user and stop.

### 2. Branch check

If the current branch is `main` or `master`:

1. Analyze the diff to categorize the work (feature, fix, refactor, docs, test, chore)
2. Suggest a branch name using the convention:
   - `feat/<slug>` — new functionality
   - `fix/<slug>` — bug fix
   - `refactor/<slug>` — restructuring without behavior change
   - `docs/<slug>` — documentation only
   - `test/<slug>` — test only
   - `chore/<slug>` — maintenance, deps, config
3. Use `AskUserQuestion` with a selector: "You're on main. Want me to move these changes to `<suggested-branch>`?" Options: the suggested branch name, an alternative branch name if applicable, and "Stay on main". 
4. If they pick a branch: `git checkout -b <branch>` — uncommitted changes carry over automatically

### 3. Decide if docs need updating

Analyze the diff and classify:

**Update docs when:**
- New feature or public API change
- CLI command added, renamed, or removed
- Configuration or setup changes
- Breaking changes
- New agent or skill added
- Architecture changes

**Skip docs when:**
- Test-only changes
- Internal refactors with no public impact
- Typo fixes or comment changes
- Work-in-progress / partial implementation

When skipping, tell the user why: "Changes are test-only — skipping doc updates."

### 4. Update docs (when applicable)

Determine which files need updates:

| File | Update when |
|------|------------|
| `README.md` | Public API, CLI, setup, or usage changes |
| `CHANGELOG.md` | Any user-facing change (features, fixes, breaking) |
| `CLAUDE.md` | Project conventions, architecture, or tooling changes |

For each file that needs updating:
1. Read its current content
2. Read the diff to understand what changed

Build a task description that includes:
- A summary of what changed (from the diff)
- Which sections of each doc are affected
- What specifically to add, update, or remove

Dispatch a single editor agent for all docs:

1. Spawn an Agent tool call with:
   - `subagent_type: "codemonkeys-code-editor"` (enforces file-only tools from AGENT.md frontmatter)
   - `prompt`: `"\n\n## Task\n\n"` + task description (which docs to update and how)
2. After the agent completes, verify with `git diff`.

(No language guidelines needed for markdown doc updates.)

Only include files that actually need updates — don't pass all three every time.

### 5. Stage and commit

1. Stage all changes (source + updated docs): `git add <specific files>`
2. Generate a commit message:
   - First line: `<type>: <concise description>` (under 72 chars)
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
   - Blank line, then body with bullet points if multiple changes
3. Show the user the staged files and proposed commit message
4. Use `AskUserQuestion` with a selector to ask for approval. Options: "Commit", "Edit message", "Cancel".
5. Commit (do NOT push — wait for explicit ask)

### 6. Post-commit

After a successful commit:
1. Show the commit hash and message
2. Show `git log --oneline -3` for context
3. Use `AskUserQuestion` with a selector: "Want me to push to origin?" Options: "Push", "Skip".
4. If they pick Push: `git push -u origin <branch>` (use `-u` if no upstream is set)

## Rules

- Never commit without showing the user what will be committed and getting approval.
- Never push without asking — always offer, never auto-push.
- Never delete branches without asking — after a merge to main, use `AskUserQuestion` with a selector: "Delete the feature branch?" Options: "Delete local + remote", "Delete local only", "Keep branch".
- Never stage `.env`, credentials, or secrets. Warn if any appear in the diff.
- If the docs agent fails or produces bad output, skip the doc updates and proceed with the commit — don't block the commit on docs.
- Keep commit messages concise. The first line is the most important part.
