"""Tests for structured executive conclusions (Milestone 9 Phase 9d)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.operational_intelligence.executive_conclusions import ExecutiveConclusionEngine
from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import EvidenceItem, Finding
from src.operational_intelligence.operational_assessment import (
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
    description: str,
    metric_name: str = "attendance_rate",
) -> Finding:
    return Finding(
        finding_id=finding_id,
        finding_type=finding_type,
        source_tool=f"{finding_type}_analysis",
        title=f"{finding_type.title()} finding",
        description=description,
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


class TestExecutiveConclusionEngine:
    def test_empty_theme_list_returns_empty_conclusions(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_HEALTHY,
            rationale="• No findings were identified.",
        )

        conclusions = ExecutiveConclusionEngine().build([], assessment)

        assert conclusions == []

    def test_single_theme_produces_one_conclusion(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="variance",
            severity="MEDIUM",
            description="Variance across school groups was detected for attendance_rate.",
        )
        theme = _make_theme(
            theme_id="theme-metric-attendance_rate",
            theme_label="attendance_rate",
            findings=[finding],
        )
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_NEEDS_ATTENTION,
            rationale="• Medium severity findings detected.",
            supporting_finding_ids=["finding-0"],
            supporting_theme_ids=["theme-metric-attendance_rate"],
        )

        conclusions = ExecutiveConclusionEngine().build([theme], assessment)

        assert len(conclusions) == 1
        assert conclusions[0].conclusion_id == "conclusion-0"
        assert conclusions[0].headline == "Needs Attention: attendance_rate"
        assert conclusions[0].assessment_level == ASSESSMENT_NEEDS_ATTENTION
        assert conclusions[0].primary_theme == "theme-metric-attendance_rate"
        assert conclusions[0].supporting_finding_ids == ["finding-0"]
        assert conclusions[0].supporting_theme_ids == ["theme-metric-attendance_rate"]
        assert conclusions[0].evidence_summary == [
            "Variance across school groups was detected for attendance_rate."
        ]

    def test_multiple_themes_produce_one_conclusion_each(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="trend",
                        severity="LOW",
                        description="Attendance declined over the analysed period.",
                    )
                ],
            ),
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="variance",
                        severity="MEDIUM",
                        description="Defect totals varied across production lines.",
                        metric_name="defects",
                    )
                ],
            ),
        ]
        assessment = OperationalAssessmentEngine().assess(themes)

        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        assert len(conclusions) == 2
        assert [conclusion.conclusion_id for conclusion in conclusions] == [
            "conclusion-0",
            "conclusion-1",
        ]
        assert conclusions[0].primary_theme == "theme-metric-attendance_rate"
        assert conclusions[1].primary_theme == "theme-metric-defects"

    def test_healthy_assessment_headline(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_HEALTHY,
            rationale="• No findings were identified.",
        )

        conclusions = ExecutiveConclusionEngine().build([], assessment)

        assert conclusions == []

    def test_requires_monitoring_assessment_headline(self):
        theme = _make_theme(
            theme_id="theme-metric-defects",
            theme_label="defects",
            findings=[
                _make_finding(
                    finding_id="finding-0",
                    finding_type="snapshot",
                    severity="LOW",
                    description="Current defects remain broadly in line with historical baseline.",
                    metric_name="defects",
                )
            ],
        )
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_REQUIRES_MONITORING,
            rationale="• Only low-severity findings were identified.",
            supporting_finding_ids=["finding-0"],
            supporting_theme_ids=["theme-metric-defects"],
        )

        conclusions = ExecutiveConclusionEngine().build([theme], assessment)

        assert conclusions[0].headline == "Requires Monitoring: defects"

    def test_needs_attention_assessment_headline(self):
        theme = _make_theme(
            theme_id="theme-metric-attendance_rate",
            theme_label="attendance_rate",
            findings=[
                _make_finding(
                    finding_id="finding-0",
                    finding_type="anomaly",
                    severity="HIGH",
                    description="Nineteen unusual attendance records were detected.",
                )
            ],
        )
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_NEEDS_ATTENTION,
            rationale="• Medium severity findings detected.",
            supporting_finding_ids=["finding-0"],
            supporting_theme_ids=["theme-metric-attendance_rate"],
        )

        conclusions = ExecutiveConclusionEngine().build([theme], assessment)

        assert conclusions[0].headline == "Needs Attention: attendance_rate"
        assert conclusions[0].evidence_summary == [
            "Nineteen unusual attendance records were detected."
        ]

    def test_evidence_summary_uses_finding_descriptions_in_order(self):
        theme = _make_theme(
            theme_id="theme-metric-attendance_rate",
            theme_label="attendance_rate",
            findings=[
                _make_finding(
                    finding_id="finding-0",
                    finding_type="trend",
                    severity="LOW",
                    description="Attendance declined over the analysed period.",
                ),
                _make_finding(
                    finding_id="finding-1",
                    finding_type="anomaly",
                    severity="HIGH",
                    description="Nineteen unusual attendance records were detected.",
                ),
                _make_finding(
                    finding_id="finding-2",
                    finding_type="snapshot",
                    severity="LOW",
                    description="Current attendance remains broadly in line with historical baseline.",
                ),
            ],
        )
        assessment = OperationalAssessmentEngine().assess([theme])

        conclusions = ExecutiveConclusionEngine().build([theme], assessment)

        assert conclusions[0].evidence_summary == [
            "Attendance declined over the analysed period.",
            "Nineteen unusual attendance records were detected.",
            "Current attendance remains broadly in line with historical baseline.",
        ]

    def test_supporting_ids_match_theme(self):
        theme = _make_theme(
            theme_id="theme-metric-attendance_rate",
            theme_label="attendance_rate",
            findings=[
                _make_finding(
                    finding_id="finding-0",
                    finding_type="variance",
                    severity="MEDIUM",
                    description="Variance detected.",
                ),
                _make_finding(
                    finding_id="finding-1",
                    finding_type="trend",
                    severity="LOW",
                    description="Trend observed.",
                ),
            ],
        )
        assessment = OperationalAssessmentEngine().assess([theme])

        conclusions = ExecutiveConclusionEngine().build([theme], assessment)

        assert conclusions[0].supporting_finding_ids == ["finding-0", "finding-1"]
        assert conclusions[0].supporting_theme_ids == ["theme-metric-attendance_rate"]

    def test_deterministic_ordering(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="trend",
                        severity="LOW",
                        description="Trend observed.",
                    )
                ],
            ),
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="variance",
                        severity="MEDIUM",
                        description="Variance detected.",
                        metric_name="defects",
                    )
                ],
            ),
        ]
        assessment = OperationalAssessmentEngine().assess(themes)
        engine = ExecutiveConclusionEngine()

        assert engine.build(themes, assessment) == engine.build(themes, assessment)

    def test_rejects_invalid_inputs(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_HEALTHY,
            rationale="• No findings were identified.",
        )

        with pytest.raises(ValueError, match="themes must be a list"):
            ExecutiveConclusionEngine().build("not a list", assessment)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="assessment must be an OperationalAssessment"):
            ExecutiveConclusionEngine().build([], "not an assessment")  # type: ignore[arg-type]

    def test_module_does_not_import_pandas(self):
        module_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "operational_intelligence"
            / "executive_conclusions.py"
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
