"""Tests for operational assessment (Milestone 9 Phase 9c)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import EvidenceItem, Finding
from src.operational_intelligence.operational_assessment import (
    ASSESSMENT_CRITICAL,
    ASSESSMENT_HEALTHY,
    ASSESSMENT_NEEDS_ATTENTION,
    ASSESSMENT_REQUIRES_MONITORING,
    OperationalAssessment,
    OperationalAssessmentEngine,
)


pytestmark = pytest.mark.unit


def _make_finding(
    *,
    finding_id: str,
    finding_type: str,
    severity: str,
    metric_name: str = "attendance_rate",
) -> Finding:
    return Finding(
        finding_id=finding_id,
        finding_type=finding_type,
        source_tool=f"{finding_type}_analysis",
        title=f"{finding_type.title()} finding",
        description=f"{finding_type.title()} description.",
        severity=severity,
        confidence="MEDIUM",
        evidence=[
            EvidenceItem(
                description=f"Evidence for {metric_name}",
                metric_name=metric_name,
                metric_value=1.0,
                supporting_context={"aggregation": "mean"},
            )
        ],
    )


def _make_theme(
    *,
    theme_id: str,
    theme_label: str,
    findings: list[Finding],
) -> ExecutiveTheme:
    return ExecutiveTheme(
        theme_id=theme_id,
        theme_label=theme_label,
        finding_ids=[finding.finding_id for finding in findings if finding.finding_id],
        findings=findings,
    )


class TestOperationalAssessmentModel:
    def test_rejects_invalid_assessment_level(self):
        with pytest.raises(ValueError, match="assessment_level must be one of"):
            OperationalAssessment(
                assessment_level="Unknown",
                rationale="Invalid level.",
            )


class TestOperationalAssessmentEngine:
    def test_no_findings_is_healthy(self):
        assessment = OperationalAssessmentEngine().assess([])

        assert assessment.assessment_level == ASSESSMENT_HEALTHY
        assert "No findings were identified." in assessment.rationale
        assert assessment.supporting_finding_ids == []
        assert assessment.supporting_theme_ids == []

    def test_one_low_finding_requires_monitoring(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="trend",
            severity="LOW",
        )
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[finding],
            )
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_REQUIRES_MONITORING
        assert "Only low-severity findings were identified." in assessment.rationale
        assert assessment.supporting_finding_ids == ["finding-0"]
        assert assessment.supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_one_medium_finding_needs_attention(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="variance",
            severity="MEDIUM",
        )
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[finding],
            )
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_NEEDS_ATTENTION
        assert "Medium severity findings detected." in assessment.rationale
        assert assessment.supporting_finding_ids == ["finding-0"]
        assert assessment.supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_one_high_finding_is_critical(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="anomaly",
            severity="HIGH",
        )
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[finding],
            )
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_CRITICAL
        assert "High severity anomaly findings detected." in assessment.rationale
        assert assessment.supporting_finding_ids == ["finding-0"]
        assert assessment.supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_mixed_severities_prioritises_critical(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="trend",
                        severity="LOW",
                    ),
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="anomaly",
                        severity="HIGH",
                    ),
                ],
            ),
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-2",
                        finding_type="variance",
                        severity="MEDIUM",
                        metric_name="defects",
                    )
                ],
            ),
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_CRITICAL
        assert assessment.supporting_finding_ids == ["finding-1"]
        assert assessment.supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_multiple_low_findings_across_themes_needs_attention(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="trend",
                        severity="LOW",
                    )
                ],
            ),
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="snapshot",
                        severity="LOW",
                        metric_name="defects",
                    )
                ],
            ),
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_NEEDS_ATTENTION
        assert "Multiple operational themes require attention." in assessment.rationale
        assert assessment.supporting_finding_ids == ["finding-0", "finding-1"]
        assert assessment.supporting_theme_ids == [
            "theme-metric-attendance_rate",
            "theme-metric-defects",
        ]

    def test_medium_and_low_mixed_uses_medium_rule(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="variance",
                        severity="MEDIUM",
                    ),
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="trend",
                        severity="LOW",
                    ),
                ],
            )
        ]

        assessment = OperationalAssessmentEngine().assess(themes)

        assert assessment.assessment_level == ASSESSMENT_NEEDS_ATTENTION
        assert assessment.supporting_finding_ids == ["finding-0"]
        assert assessment.supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_deterministic_ordering_is_preserved(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="trend",
                        severity="LOW",
                    )
                ],
            ),
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="snapshot",
                        severity="LOW",
                        metric_name="defects",
                    ),
                    _make_finding(
                        finding_id="finding-2",
                        finding_type="anomaly",
                        severity="LOW",
                        metric_name="defects",
                    ),
                ],
            ),
        ]

        engine = OperationalAssessmentEngine()
        first = engine.assess(themes)
        second = engine.assess(themes)

        assert first == second
        assert first.supporting_finding_ids == ["finding-0", "finding-1", "finding-2"]

    def test_rejects_non_list_input(self):
        with pytest.raises(ValueError, match="themes must be a list"):
            OperationalAssessmentEngine().assess("not a list")  # type: ignore[arg-type]

    def test_module_does_not_import_pandas(self):
        module_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "operational_intelligence"
            / "operational_assessment.py"
        )
        parsed = ast.parse(module_path.read_text(encoding="utf-8"))

        imported_names: set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module.split(".")[0])

        assert "pandas" not in imported_names
