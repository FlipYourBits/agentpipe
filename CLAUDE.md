# Codemonkeys

Python and JavaScript/TypeScript code review and development toolkit powered by Claude Agent SDK. Engineering judgment, workflow, and standards encoded as agent pipelines.

## Agent Architecture

Two generic agents handle all per-file work, dispatched by file extension across multiple languages:

- **`code_reviewer`** — reads a file and returns structured findings (code quality, security, conventions). Supports Python, JavaScript, and TypeScript.
- **`code_editor`** — applies edits to a file based on instructions or findings. Supports Python, JavaScript, and TypeScript.

Cross-file design concerns are handled by a third agent:

- **`python_architecture_reviewer`** — reviews multiple files for structural and design issues (coupling, cohesion, layering)

Open-ended research is handled by a fourth agent:

- **`researcher`** — autonomous web research agent that investigates topics and produces SKILL.md or markdown reports

The CLI exposes six commands: `review`, `edit`, `implement`, `architecture`, `research`, `init`.

