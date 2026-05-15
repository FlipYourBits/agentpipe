# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `python_file_reviewer` agent — generic per-file review dispatched by file extension, replacing all specialized per-file reviewer agents
- `python_file_editor` agent — generic per-file editor dispatched by file extension, replacing all specialized per-file writer/fixer agents
- `file_printer` display module — replaces `live.py` and `results.py`
- Audit schema tests for structured output validation
- Docstrings on feature planner models (`PlanOption`, `PlanItem`, `FeaturePlan`, `PlannerOutput`)
- `select_all` field on `TriageResult` — when the user wants everything, avoids listing every index
- `prompt` parameter on `run_triage()` for custom user-facing prompts
- Large system prompts (>100K chars) automatically written to temp files (`SystemPromptFile`) to avoid prompt size limits
- Structured-output agents receive an explicit "stop after output" instruction to prevent trailing text
- Audit findings exported to a `findings.md` markdown file in the log directory
- Per-file parallel code fixes in audit workflow, replacing the sequential iteration loop
- Error recovery in branch management — stash is restored if `git checkout -b` fails
- `python_test_quality_reviewer` agent exported from `codemonkeys.agents`
- `Literal` types on agent schema fields (`severity`, `category`, `confidence`, `action`) for stricter validation
- `print_patch()` utility in `codemonkeys.core.diff` for displaying patch files with syntax-highlighted diff output
- CLI entry point — install the package and run workflows as `codemonkeys <command>` (e.g., `codemonkeys review`, `codemonkeys feature`, `codemonkeys bugfix`)
- Patch file generation after code changes in bugfix, commit, feature, and refactor workflows
- `integration_seams` category in the design review prompt for catching pattern-inconsistent new code
- `max_stop_retries` field on `AgentDefinition` (default 2) to cap consecutive Stop-hook failures and prevent infinite retry loops
- Concurrency control for the test-writer workflow via `CODEMONKEYS_MAX_PARALLEL_AGENTS` env var (default 4)
- `python_test_writer` agent now reads existing test files and edits them instead of overwriting from scratch
- `PERFORMANCE_REVIEW` prompt added to code reviewer (file and diff modes) with new `PERFORMANCE` finding category
- Dependency audit via `pip-audit` in the audit workflow — vulnerabilities surface as high-severity findings
- Diff truncation (100K char limit) for reviewer and docs writer agents to prevent prompt overflow
- `finalize_changes()` shared finalizer — all workflows (audit, bugfix, feature) now auto-update docs and commit at the end
- Docs writer accepts a `context` parameter describing why changes were made, for better changelog entries

### Changed
- 11 specialized agents consolidated into 2 generic agents (`python_file_reviewer`, `python_file_editor`) plus `python_architecture_reviewer` for cross-file analysis
- Agent registry renamed: `AUDITORS` → `REVIEWERS`, `get_auditor()` → `get_reviewer()`
- CLI rewritten with commands: `review`, `edit`, `implement`, `architecture`, `init`
- `PlannerOutput.ready` renamed to `PlannerOutput.is_ready` for clarity
- `python_code_writer` no longer accepts a `config` parameter or runs automated hooks (lint, test, typecheck); callers manage checks externally
- `python_code_reviewer` file mode requires `content=` parameter; file content is embedded in the prompt and Read/Grep tools are removed
- Audit workflow code fixes run per-file in parallel instead of through a single iteration loop
- Audit findings displayed as a severity/source summary with a link to the full markdown report, replacing the Rich table
- Prompt checklist headers simplified — removed redundant "Review Checklist" prefixes and introductory paragraphs
- `input()` calls in iteration and triage replaced with async `asyncio.to_thread`/`run_in_executor` to avoid blocking the event loop
- `InteractiveSession.send()` returns only events from the current turn, not all historical events
- Missing `landlock` package on Linux now raises `RuntimeError` instead of logging a warning
- `discover_files()` raises on git errors (`check=True`)
- Test quality reviewer "What to Look For" section consolidated into the shared `TEST_QUALITY` prompt
- Feature workflow uses `WorkflowState.load_or_new` instead of `prompt_resume`
- Workflow modules renamed to shorter names: `bugfix`, `commit`, `feature`, `refactor`, `review`, `test_coverage`
- Architecture reviewer no longer includes the hardening checklist; relevant integration seam checks folded into the design review prompt
- Stop hooks now respect `max_stop_retries` — after that many consecutive failures the hook lets the agent finish
- `build_check_hooks` accepts an optional `max_stop_retries` parameter forwarded from the agent definition
- Audit workflow splits findings by type: coverage findings go to `test_writer` (parallel, self-verifying), code findings go to `code_writer` (iteration loop)
- Audit coverage analysis runs asynchronously instead of blocking the event loop
- Workflow functions (`run_audit`, `run_bugfix`, `run_commit`) now accept keyword args directly instead of parsing argv lists
- `stage_and_commit()` takes an explicit file list instead of `git add -A` for safer staging
- Runner internals refactored — extracted `_build_options()`, `_process_message()`, and `_build_run_result()` to eliminate duplication between `run_agent()` and `InteractiveSession`

### Removed
- Agents: `agent_log_reviewer`, `python_bug_investigator`, `python_code_reviewer`, `python_code_writer`, `python_docs_writer`, `python_feature_planner`, `python_file_auditor`, `python_test_quality_reviewer`, `python_test_writer`, `spec_compliance_reviewer`, `triage`
- `config.py`, `live.py`, `results.py` and their associated tests
- `config` parameter and automated hooks (PostToolUse lint, Stop test/typecheck) from `python_code_writer`
- Iteration loop from audit workflow code fixes — replaced by parallel per-file execution
- `docs/plans/2026-05-11-workflow-redesign.md` plan file
- `HARDENING_CHECKLIST` prompt module — error paths, edge cases, and defensive boundaries moved to per-file reviewers
- Standalone `AGENTS_ARCHITECTURE.md`, `TESTED_AGENTS.md`, and `TODO.md` documentation files
- `build_tool_hooks()` backwards-compatibility alias — use `build_permission_hooks()` instead
- `_has_bare_tool()` internal helper (no longer needed)
- `AuditArgs`, `BugFixArgs`, `CommitArgs` dataclasses and their `parse_args` functions — workflows use keyword args now

### Fixed
- Triage agent no longer crashes when selected indices are out of bounds
- `_annotate_uncovered` now handles `\r\n` (Windows) line endings correctly — previously the `# << UNCOVERED` annotation was inserted between `\r` and `\n`, corrupting the line ending
