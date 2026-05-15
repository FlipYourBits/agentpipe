"""Tests for audit finding schemas."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codemonkeys.core.types import AuditFinding, AuditResults, FileReviewResult


def test_audit_finding_minimal() -> None:
    f = AuditFinding(
        file="codemonkeys/cli.py",
        category="naming",
        severity="medium",
        title="Unclear variable name",
        description="Variable 'x' does not describe intent.",
    )
    assert f.file == "codemonkeys/cli.py"
    assert f.line is None
    assert f.suggestion is None


def test_audit_finding_full() -> None:
    f = AuditFinding(
        file="codemonkeys/cli.py",
        line=42,
        category="security",
        severity="high",
        title="Command injection risk",
        description="User input passed directly to subprocess.",
        suggestion="Use a list of arguments instead of shell=True.",
    )
    assert f.line == 42
    assert f.suggestion is not None


def test_audit_finding_invalid_severity() -> None:
    with pytest.raises(ValidationError):
        AuditFinding(
            file="x.py",
            category="naming",
            severity="critical",
            title="t",
            description="d",
        )


def test_audit_finding_serializes_to_json() -> None:
    f = AuditFinding(
        file="x.py", category="naming", severity="low",
        title="t", description="d",
    )
    data = json.loads(f.model_dump_json())
    assert data["file"] == "x.py"
    assert data["severity"] == "low"
    assert data["line"] is None


def test_file_review_result_empty() -> None:
    r = FileReviewResult(findings=[])
    assert r.findings == []


def test_file_review_result_with_findings() -> None:
    f = AuditFinding(
        file="x.py", category="naming", severity="low",
        title="t", description="d",
    )
    r = FileReviewResult(findings=[f])
    assert len(r.findings) == 1


def test_audit_results_empty() -> None:
    r = AuditResults(files_reviewed=["a.py"], findings=[])
    assert r.files_reviewed == ["a.py"]
    assert r.findings == []


def test_audit_results_serializes_round_trip() -> None:
    f = AuditFinding(
        file="a.py", line=10, category="security", severity="high",
        title="Issue", description="Details", suggestion="Fix it",
    )
    r = AuditResults(files_reviewed=["a.py", "b.py"], findings=[f])
    data = json.loads(r.model_dump_json())
    r2 = AuditResults.model_validate(data)
    assert r2.files_reviewed == r.files_reviewed
    assert len(r2.findings) == 1
    assert r2.findings[0].file == "a.py"


def test_audit_results_multiple_files() -> None:
    findings = [
        AuditFinding(file="a.py", category="naming", severity="low", title="t1", description="d1"),
        AuditFinding(file="b.py", category="security", severity="high", title="t2", description="d2"),
    ]
    r = AuditResults(files_reviewed=["a.py", "b.py"], findings=findings)
    assert len(r.findings) == 2
