"""Tests for priority action generation (Milestone 9 Phase 9e)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.operational_intelligence.executive_conclusions import (
    ExecutiveConclusionEngine,
)
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
from src.operational_intelligence.priority_actions import (
    MAX_PRIORITY_ACTIONS,
    PriorityActionEngine,
    _CAUSATION_BLACKLIST,
)


pytestmark = pytest.mark.unit


def _make_finding(
    *,
    finding_id: str,
    finding_type: str,
    severity: str,
    metric_name: str = "attendance_rate",
    description: str | None = None,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        finding_type=finding_type,
        source_tool=f"{finding_type}_analysis",
        title=f"{finding_type.title()} finding",
        description=description or f"{finding_type.title()} description.",
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


def _build_actions(themes: list[ExecutiveTheme]) -> list:
    assessment = OperationalAssessmentEngine().assess(themes)
    conclusions = ExecutiveConclusionEngine().build(themes, assessment)
    return PriorityActionEngine().build(themes, assessment, conclusions)


class TestPriorityActionEngine:
    def test_no_themes_returns_empty_list(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_HEALTHY,
            rationale="• No findings were identified.",
        )

        actions = PriorityActionEngine().build([], assessment, [])

        assert actions == []

    def test_healthy_with_no_findings_returns_empty_list(self):
        actions = _build_actions([])

        assert actions == []

    def test_critical_assessment_uses_immediate_urgency(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
                    )
                ],
            )
        ]
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        actions = PriorityActionEngine().build(themes, assessment, conclusions)

        assert len(actions) == 1
        assert actions[0].urgency == "Immediate"

    def test_needs_attention_assessment_uses_soon_urgency(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="variance",
                        severity="MEDIUM",
                    )
                ],
            )
        ]
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        actions = PriorityActionEngine().build(themes, assessment, conclusions)

        assert actions[0].urgency == "Soon"

    def test_requires_monitoring_assessment_uses_monitor_urgency(self):
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
            )
        ]
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        actions = PriorityActionEngine().build(themes, assessment, conclusions)

        assert actions[0].urgency == "Monitor"

    def test_anomaly_action_wording(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
                    )
                ],
            )
        ]

        actions = _build_actions(themes)

        assert actions[0].action == (
            "Investigate anomalous records linked to attendance_rate."
        )

    def test_variance_action_wording(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="variance",
                        severity="MEDIUM",
                        metric_name="defects",
                    )
                ],
            )
        ]

        actions = _build_actions(themes)

        assert actions[0].action == "Review group differences linked to defects."

    def test_trend_action_wording(self):
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
            )
        ]

        actions = _build_actions(themes)

        assert actions[0].action == "Monitor trend movement linked to attendance_rate."

    def test_snapshot_action_wording(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="snapshot",
                        severity="LOW",
                    )
                ],
            )
        ]

        actions = _build_actions(themes)

        assert actions[0].action == (
            "Review snapshot performance for attendance_rate against baseline."
        )

    def test_deduplication_produces_one_action_per_theme(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
                    ),
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="anomaly",
                        severity="HIGH",
                    ),
                ],
            )
        ]

        actions = _build_actions(themes)

        assert len(actions) == 1
        assert actions[0].linked_finding_ids == ["finding-0", "finding-1"]

    def test_ranking_prioritises_high_severity_themes(self):
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
                        finding_type="anomaly",
                        severity="HIGH",
                        metric_name="defects",
                    )
                ],
            ),
        ]

        actions = _build_actions(themes)

        assert [action.linked_theme_ids[0] for action in actions] == [
            "theme-metric-defects",
            "theme-metric-attendance_rate",
        ]
        assert [action.rank for action in actions] == [1, 2]

    def test_ranking_prioritises_medium_theme_above_low_theme(self):
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
                        finding_type="variance",
                        severity="MEDIUM",
                        metric_name="defects",
                    )
                ],
            ),
        ]

        actions = _build_actions(themes)

        assert [action.linked_theme_ids[0] for action in actions] == [
            "theme-metric-defects",
            "theme-metric-attendance_rate",
        ]

    def test_high_severity_rationale_uses_high_not_info(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
                    )
                ],
            )
        ]

        actions = _build_actions(themes)

        assert "Based on HIGH severity anomaly finding(s)" in actions[0].rationale
        assert "INFO severity" not in actions[0].rationale

    def test_output_capped_at_five_actions(self):
        themes = [
            _make_theme(
                theme_id=f"theme-metric-metric_{index}",
                theme_label=f"metric_{index}",
                findings=[
                    _make_finding(
                        finding_id=f"finding-{index}",
                        finding_type="trend",
                        severity="LOW",
                        metric_name=f"metric_{index}",
                    )
                ],
            )
            for index in range(MAX_PRIORITY_ACTIONS + 1)
        ]

        actions = _build_actions(themes)

        assert len(actions) == MAX_PRIORITY_ACTIONS
        assert actions[-1].rank == MAX_PRIORITY_ACTIONS

    def test_linked_finding_and_theme_ids_populated(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="variance",
                        severity="MEDIUM",
                    )
                ],
            )
        ]

        actions = _build_actions(themes)

        assert actions[0].linked_finding_ids == ["finding-0"]
        assert actions[0].linked_theme_ids == ["theme-metric-attendance_rate"]

    def test_linked_conclusion_ids_populated_when_available(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="variance",
                        severity="MEDIUM",
                    )
                ],
            )
        ]
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        actions = PriorityActionEngine().build(themes, assessment, conclusions)

        assert actions[0].linked_conclusion_ids == ["conclusion-0"]

    def test_deterministic_output(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
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
                        metric_name="defects",
                    )
                ],
            ),
        ]

        engine = PriorityActionEngine()
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)

        first = engine.build(themes, assessment, conclusions)
        second = engine.build(themes, assessment, conclusions)

        assert first == second

    def test_no_causation_language_in_actions(self):
        themes = [
            _make_theme(
                theme_id="theme-metric-attendance_rate",
                theme_label="attendance_rate",
                findings=[
                    _make_finding(
                        finding_id="finding-0",
                        finding_type="anomaly",
                        severity="HIGH",
                    ),
                    _make_finding(
                        finding_id="finding-1",
                        finding_type="variance",
                        severity="MEDIUM",
                    ),
                    _make_finding(
                        finding_id="finding-2",
                        finding_type="trend",
                        severity="LOW",
                    ),
                    _make_finding(
                        finding_id="finding-3",
                        finding_type="snapshot",
                        severity="LOW",
                    ),
                ],
            )
        ]

        actions = _build_actions(themes)

        for action in actions:
            combined = f"{action.action} {action.rationale}".lower()
            for phrase in _CAUSATION_BLACKLIST:
                assert phrase not in combined

    def test_rejects_invalid_inputs(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_HEALTHY,
            rationale="• No findings were identified.",
        )

        with pytest.raises(ValueError, match="themes must be a list"):
            PriorityActionEngine().build("not a list", assessment, [])  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="assessment must be an OperationalAssessment"):
            PriorityActionEngine().build([], "not an assessment", [])  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="conclusions must be a list"):
            PriorityActionEngine().build([], assessment, "not a list")  # type: ignore[arg-type]

    def test_module_does_not_import_pandas(self):
        module_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "operational_intelligence"
            / "priority_actions.py"
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
