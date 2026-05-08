"""Spec compliance reviewer — compares implementation against a plan."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition


class PlanStep(BaseModel):
    description: str
    files: list[str]


class ComplianceFinding(BaseModel):
    category: str
    severity: str
    spec_step: str | None = None
    files: list[str]
    title: str
    description: str
    suggestion: str | None = None


class ComplianceResult(BaseModel):
    spec_title: str
    steps_implemented: int
    steps_total: int
    findings: list[ComplianceFinding]


def make_spec_compliance_reviewer(
    *,
    spec_title: str,
    spec_description: str,
    steps: list[PlanStep],
    files: list[str],
    unplanned_files: list[str],
    model: str = "opus",
) -> AgentDefinition:
    """Create a spec compliance reviewer for a completed feature."""
    steps_text = "\n".join(
        f"- **Step {i + 1}:** {step.description}\n"
        f"  Files: {', '.join(f'`{f}`' for f in step.files) or '(none specified)'}"
        for i, step in enumerate(steps)
    )

    files_text = "\n".join(f"- `{f}`" for f in files)

    unplanned_text = (
        "\n".join(f"- `{f}`" for f in unplanned_files)
        if unplanned_files
        else "(none — all changed files are in the spec)"
    )

    safe_title = spec_title.replace('"', '\\"')

    return AgentDefinition(
        name=f"spec_compliance_reviewer:{safe_title}",
        model=model,
        system_prompt=f"""\
You review whether an implementation matches its specification. Read the spec,
then read the implementation files, and report any gaps between intent and reality.

## Guardrails

You are a **read-only reviewer**. Do NOT modify, create, or delete any files.
Do NOT run commands, install packages, or modify git state. Your only job is
to analyze and report findings.

## The Spec

**Title:** {spec_title}

**Description:** {spec_description}

### Planned Steps

{steps_text}

## Implementation Files

{files_text}

## Unplanned Files

These files changed but are NOT listed in any spec step:

{unplanned_text}

## Output Format

Return a JSON object with:
- `spec_title`: the spec title
- `steps_implemented`: count of steps actually built (int)
- `steps_total`: {len(steps)}
- `findings`: array where each finding has: category, severity (high/medium/low),
  spec_step (step description or null), files, title, description, suggestion (or null).

## Checklist

### completeness
Is every spec step implemented? Read the implementation files and verify that
each planned step was actually built.

### scope_creep
Do unplanned files contain feature work not in the spec, or are they reasonable
supporting changes?

### contract_compliance
Do function signatures, schemas, and interfaces match what the spec described?

### behavioral_fidelity
Does the code do what the spec says, or does it do something subtly different?

### test_coverage
Does each spec step have corresponding tests?

## Rules

- Only report findings at 80%+ confidence
- `spec_step` is null only for findings not tied to a specific step
- Read the implementation files to verify — do not guess from file names
- If the implementation perfectly matches the spec, return empty findings
- Count `steps_implemented` by reading the code, not by counting files""",
        tools=["Read", "Grep"],
        output_schema=ComplianceResult,
    )
