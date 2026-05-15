---
name: codemonkeys-visualize
description: Use when the user asks to visualize, diagram, or display something in the browser, or when another skill needs to present architecture diagrams, side-by-side comparisons, audit findings, UI mockups, data flows, or any design artifact — generates single-file HTML+JS pages
---

Create a self-contained HTML page that visualizes something the user needs to see. Write the file and open it in the browser so the user can review it interactively.

Can be invoked directly by the user (e.g. `/codemonkeys-visualize the data flow for the review pipeline`) or by other skills that need visual output. When called with a description, use it as-is — read relevant code or files if needed for accuracy, then generate the visual.

## Process

1. **Decide what to show.** If the user provided a description, use that. Otherwise, determine what specific visual will help the user make a decision or understand the design. If the description is vague, read relevant code to ground the visual in reality before generating.
2. **Consult the type selection matrix.** Determine which type file to read and whether a toolkit file is needed.
3. **Read the relevant files.** Read files from this skill directory as the matrix indicates. Start with the type file, add toolkit files if the matrix says to.
4. **Composite the HTML.** Start with the base template below. Add toolkit JS if needed. Add type-specific HTML/CSS/JS from the type file. The result is always a single self-contained HTML file.
5. **Write and open.** Write to `.codemonkeys/visuals/YYYYMMDD-HHMMSS_<descriptive-name>.html`. Create the directory if needed. Open in browser:
   - Linux: `xdg-open <file>`
   - macOS: `open <file>`
   - Windows (Git Bash / WSL): `start <file>` or `wslview <file>`
   - Fallback: `uv run python -m webbrowser <file>`
6. **Ask the user.** Reference what they're seeing and ask the question.

## Type Selection Matrix

Read the type file that matches what you're showing. Also read toolkit files when indicated.

| What you're showing | Type file | Also read |
|---|---|---|
| Components and their relationships | `types/architecture-diagram.md` | `svg-toolkit.md` |
| Data moving through a pipeline | `types/data-flow.md` | `svg-toolkit.md` |
| 2-3 design options to choose from | `types/side-by-side.md` | — |
| Interface layout or wireframe | `types/ui-mockup.md` | — |
| Module/file dependencies | `types/component-map.md` | `svg-toolkit.md` |
| Phases, milestones, schedule | `types/timeline.md` | `svg-toolkit.md` only if milestones have dependency arrows |
| Hierarchical structure (files, orgs) | `types/tree-hierarchy.md` | `interactivity.md` |
| Structured data to explore | `types/table-view.md` | `interactivity.md` |
| Before vs after changes | `types/diff-view.md` | — |
| Numbers, trends, KPIs | `types/metrics-dashboard.md` | — |
| Code with annotations | `types/code-display.md` | — |

If a visual doesn't fit any type, composite directly from the design system and toolkits below.

## Design System

Every generated HTML file starts from this base template. All colors use CSS custom properties so the entire palette is controlled from one place.

### Base Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><!-- descriptive title --></title>
    <style>
        :root {
            /* Backgrounds — layered depth */
            --bg-page: #0f1117;
            --bg-card: #161b22;
            --bg-elevated: #1c2333;

            /* Borders */
            --border-default: #30363d;
            --border-active: #58a6ff;

            /* Text */
            --text-heading: #f0f3f6;
            --text-body: #e1e4e8;
            --text-secondary: #c9d1d9;
            --text-muted: #8b949e;

            /* Semantic */
            --color-success: #3fb950;
            --color-warning: #d29922;
            --color-error: #f85149;
            --color-info: #58a6ff;

            /* Category — 8 hues for distinguishing node types */
            --cat-blue: #58a6ff;
            --cat-green: #3fb950;
            --cat-purple: #bc8cff;
            --cat-orange: #d29922;
            --cat-red: #f85149;
            --cat-cyan: #39d2c0;
            --cat-pink: #f778ba;
            --cat-yellow: #e3b341;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: var(--bg-page);
            color: var(--text-body);
            padding: 2rem;
            line-height: 1.6;
        }

        h1 { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-heading); }
        h2 { font-size: 1.1rem; margin: 1.5rem 0 0.75rem; color: var(--text-secondary); }

        .label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .node {
            display: inline-block;
            background: var(--bg-elevated);
            border: 1px solid var(--border-default);
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
            font-size: 0.85rem;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-default);
            border-radius: 8px;
            padding: 1.5rem;
        }
        .badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 600;
        }

        code {
            background: var(--bg-elevated);
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
            font-size: 0.85rem;
            color: var(--cat-cyan);
        }

        /* Shared transitions — respect reduced motion */
        * { transition: background 0.2s ease, border-color 0.2s ease, opacity 0.2s ease, transform 0.2s ease; }
        @media (prefers-reduced-motion: reduce) {
            * { transition: none !important; animation: none !important; }
        }
    </style>
</head>
<body>
    <!-- Type-specific content here -->
    <!-- Type-specific JS here -->
</body>
</html>
```

## Rules

- Single file, no external dependencies. Everything inline.
- Dark theme by default (matches terminal workflow).
- Keep it focused — show one thing clearly, not everything at once.
- Interactive where it helps (clickable options, hover states, expandable sections) but don't over-engineer it.
- After showing the visual, always bring the conversation back to the terminal for the actual decision.
- Clean up: visuals are ephemeral aids. The user can delete `.codemonkeys/visuals/` at any time.
- Always use CSS custom properties from the design system, never hardcoded hex values.
- Always include the `prefers-reduced-motion` media query when using animations.
- SVG overlays must have `pointer-events: none` so they don't block interaction with HTML elements beneath.
- When combining zoom/pan with SVG connections, call `recalculate()` after transform changes.
- Each generated HTML file must be fully self-contained — copy all needed CSS/JS inline, even if it comes from a toolkit file.
