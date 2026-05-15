---
name: codemonkeys-research
description: Use when the user wants to research a topic, investigate a technology, read papers/docs, or generate knowledge — dispatches an autonomous research agent that searches the web, reads sources, verifies claims, and produces a SKILL.md, markdown report, or HTML visualization
---

Research a topic thoroughly and produce actionable output.

## Process

### 1. Clarify the topic

If the user's request is clear (specific topic, optionally with URLs), proceed. If vague, ask one clarifying question to narrow scope.

### 2. Ask output format

Ask the user which output format they want:
- **Claude SKILL.md** — drops into `.claude/skills/<topic>/SKILL.md`, immediately usable as a skill
- **Markdown report** — detailed report at `.codemonkeys/research/YYYYMMDD-HHMMSS_<topic>.md`
- **HTML visualization** — generates markdown report, then invokes `codemonkeys-visualize` to render it in the browser

### 3. Run the research agent

For SKILL.md or markdown:

```bash
codemonkeys research "<topic with optional URLs>" --format skill
codemonkeys research "<topic with optional URLs>" --format markdown
```

Show the exact command before running it. The agent runs on Opus and has full web access — it will search, read sources, follow links, and verify claims autonomously.

### 4. Review output

After the agent completes:

1. Read the output file
2. Show the user a summary: how many sources consulted, any confidence notes, key sections
3. If HTML format was requested, invoke the `codemonkeys-visualize` skill to render the markdown report as an interactive HTML page

### 5. Iterate (optional)

If the user wants deeper coverage on a specific section, run the research agent again with a more focused topic and merge the results manually, or edit the output file directly.

## Rules

- Always show the exact command before running it.
- The research agent is autonomous — let it run without interruption.
- For HTML output, always generate the markdown report first, then visualize.
- Do not fabricate research results yourself — always dispatch the agent.
