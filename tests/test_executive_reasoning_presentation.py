"""Tests for executive reasoning UI presentation (Milestone 10a / 10a.1 / 10a.2)."""

from __future__ import annotations

import pytest

from src.operational_intelligence.executive_conclusions import ExecutiveConclusion
from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import EvidenceItem, ExecutiveReport, Finding
from src.operational_intelligence.operational_assessment import (
    ASSESSMENT_CRITICAL,
    ASSESSMENT_REQUIRES_MONITORING,
    OperationalAssessment,
)
from src.operational_intelligence.priority_actions import PriorityAction
from src.operational_intelligence import reporting as _reporting  # noqa: F401 — model_rebuild
from ui.executive_reasoning_presentation import (
    ADDITIONAL_INVESTIGATIONS_EXPANDER_LABEL,
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
    DEFAULT_INVESTIGATION_LIMIT,
    EVIDENCE_CONSIDERED_HEADING,
    EXECUTIVE_REASONING_HEADING,
    format_analysis_overview,
    format_assessment_level_display,
    format_executive_conclusion,
    format_operational_assessment,
    format_priority_action,
    humanise_priority_action_text,
    humanise_priority_rationale,
    humanise_theme_label,
    should_show_executive_reasoning,
    should_show_executive_conclusions,
    should_show_operational_assessment,
    should_show_priority_actions,
    should_show_recommended_actions,
    split_follow_up_investigations,
    summarize_finding_evidence,
    synthesize_conclusion_insight,
)
from ui.metric_presentation import humanise_metric_name


pytestmark = pytest.mark.unit


def _legacy_report(**overrides) -> ExecutiveReport:
    report = ExecutiveReport(
        executive_summary="Operational analysis identified 1 finding(s): 0 high priority, 1 medium priority, and 0 low priority.",
        recommended_next_steps=["Review discrepancies between highest and lowest categories."],
    )
    if overrides:
        return report.model_copy(update=overrides)
    return report


def _make_finding(
    *,
    finding_id: str,
    finding_type: str,
    severity: str,
    description: str,
    metric_name: str = "units_produced",
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
                supporting_context={"aggregation": "sum"},
            )
        ],
    )


def _reasoning_report() -> ExecutiveReport:
    findings = [
        _make_finding(
            finding_id="finding-0",
            finding_type="variance",
            severity="HIGH",
            description="Variance across groups detected.",
            metric_name="defects",
        )
    ]
    return _legacy_report(
        operational_assessment=OperationalAssessment(
            assessment_level=ASSESSMENT_CRITICAL,
            rationale="• High severity variance findings detected.",
            supporting_finding_ids=["finding-0"],
            supporting_theme_ids=["theme-metric-defects"],
        ),
        executive_themes=[
            ExecutiveTheme(
                theme_id="theme-metric-defects",
                theme_label="defects",
                finding_ids=["finding-0"],
                findings=findings,
            )
        ],
        executive_conclusions=[
            ExecutiveConclusion(
                conclusion_id="conclusion-0",
                headline=f"{ASSESSMENT_CRITICAL}: defects",
                assessment_level=ASSESSMENT_CRITICAL,
                primary_theme="theme-metric-defects",
                supporting_finding_ids=["finding-0"],
                supporting_theme_ids=["theme-metric-defects"],
                evidence_summary=["Variance across groups detected."],
            )
        ],
        priority_actions=[
            PriorityAction(
                action_id="action-0",
                rank=1,
                urgency="Immediate",
                action="Review group differences linked to defects.",
                rationale="Based on HIGH severity variance finding(s) linked to defects.",
                linked_finding_ids=["finding-0"],
                linked_theme_ids=["theme-metric-defects"],
                linked_conclusion_ids=["conclusion-0"],
            )
        ],
        recommended_next_steps=["Review group differences linked to defects."],
    )


class TestExecutiveReasoningPresentationVisibility:
    def test_executive_reasoning_group_hidden_when_no_reasoning_artifacts(self):
        report = _legacy_report()

        assert should_show_executive_reasoning(report) is False

    def test_executive_reasoning_group_shown_when_reasoning_present(self):
        report = _reasoning_report()

        assert should_show_executive_reasoning(report) is True

    def test_operational_assessment_hidden_when_absent(self):
        report = _legacy_report()

        assert should_show_operational_assessment(report) is False

    def test_operational_assessment_shown_when_present(self):
        report = _reasoning_report()

        assert should_show_operational_assessment(report) is True

    def test_executive_conclusions_hidden_when_empty(self):
        report = _legacy_report(executive_conclusions=[])

        assert should_show_executive_conclusions(report) is False

    def test_executive_conclusions_shown_when_present(self):
        report = _reasoning_report()

        assert should_show_executive_conclusions(report) is True

    def test_priority_actions_hidden_when_empty(self):
        report = _legacy_report(priority_actions=[])

        assert should_show_priority_actions(report) is False

    def test_priority_actions_shown_when_present(self):
        report = _reasoning_report()

        assert should_show_priority_actions(report) is True

    def test_recommended_actions_hidden_when_priority_actions_present(self):
        report = _reasoning_report()

        assert should_show_recommended_actions(report) is False

    def test_recommended_actions_shown_for_legacy_report(self):
        report = _legacy_report()

        assert should_show_recommended_actions(report) is True


class TestExecutiveReasoningPresentationFormatting:
    def test_heading_constants(self):
        assert ANALYSIS_OVERVIEW_HEADING == "Analysis Overview"
        assert ANALYTICAL_FINDINGS_HEADING == "Analytical Findings"
        assert EXECUTIVE_REASONING_HEADING == "Executive Reasoning"

    def test_assessment_level_indicators_include_text_and_emoji(self):
        assert format_assessment_level_display(ASSESSMENT_REQUIRES_MONITORING) == (
            "🟡 Requires Monitoring"
        )
        assert format_assessment_level_display(ASSESSMENT_CRITICAL) == "🔴 Critical"
        assert "Requires Monitoring" in format_assessment_level_display(
            ASSESSMENT_REQUIRES_MONITORING
        )

    def test_analysis_overview_summarises_analytical_work_without_duplicating_assessment(
        self,
    ):
        report = _reasoning_report()
        overview = format_analysis_overview(
            findings=[report.executive_themes[0].findings[0]],
            routes=["variance_analysis", "risk_assessment"],
            report=report,
        )

        assert overview.bullets[0] == "1 analytical finding"
        assert "Variance analysis executed" in overview.bullets
        assert "Risk assessment executed" in overview.bullets
        assert overview.bullets[-1] == "High operational risk"
        assert "High severity variance findings detected." not in overview.bullets

    def test_humanise_theme_label_delegates_to_shared_metric_helper(self):
        assert humanise_theme_label("units_produced") == humanise_metric_name("units_produced")
        assert humanise_theme_label("attendance_rate") == "Attendance Rate"

    def test_operational_assessment_uses_level_display_and_explanation_only(self):
        assessment = OperationalAssessment(
            assessment_level=ASSESSMENT_REQUIRES_MONITORING,
            rationale="• Only low-severity findings were identified.",
            supporting_finding_ids=["finding-0"],
            supporting_theme_ids=["theme-metric-hours"],
        )

        presentation = format_operational_assessment(assessment)

        assert presentation.level == ASSESSMENT_REQUIRES_MONITORING
        assert presentation.level_display == "🟡 Requires Monitoring"
        assert presentation.explanation == "Only low-severity findings were identified."
        assert not hasattr(presentation, "level_heading")
        assert not hasattr(presentation, "explanation_heading")

    def test_executive_conclusions_render_synthesis_and_concise_evidence(self):
        findings = [
            _make_finding(
                finding_id="finding-0",
                finding_type="trend",
                severity="LOW",
                description="The series remained volatile over the period.",
            ),
            _make_finding(
                finding_id="finding-1",
                finding_type="variance",
                severity="MEDIUM",
                description="Variance across production lines detected.",
            ),
            _make_finding(
                finding_id="finding-2",
                finding_type="anomaly",
                severity="HIGH",
                description="38 abnormal production records identified.",
            ),
        ]
        report = _legacy_report(
            executive_themes=[
                ExecutiveTheme(
                    theme_id="theme-metric-units_produced",
                    theme_label="units_produced",
                    finding_ids=["finding-0", "finding-1", "finding-2"],
                    findings=findings,
                )
            ],
            executive_conclusions=[
                ExecutiveConclusion(
                    conclusion_id="conclusion-0",
                    headline=f"{ASSESSMENT_CRITICAL}: units_produced",
                    assessment_level=ASSESSMENT_CRITICAL,
                    primary_theme="theme-metric-units_produced",
                    supporting_finding_ids=["finding-0", "finding-1", "finding-2"],
                    supporting_theme_ids=["theme-metric-units_produced"],
                    evidence_summary=[finding.description for finding in findings],
                )
            ],
        )

        presentation = format_executive_conclusion(
            report.executive_conclusions[0],
            report,
        )

        assert presentation.title == "Units Produced"
        assert "high-severity anomalies" in presentation.insight.lower()
        assert presentation.evidence_heading == EVIDENCE_CONSIDERED_HEADING
        assert presentation.evidence_bullets == [
            "Trend analysis detected increased volatility.",
            "Variance analysis identified material differences between groups.",
            "Anomaly detection identified abnormal operational records.",
        ]
        assert "Variance across production lines detected." not in presentation.evidence_bullets
        assert "38 abnormal production records identified." not in presentation.insight

    def test_snapshot_synthesis_uses_baseline_language(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="snapshot",
            severity="LOW",
            description="Performance remained below the dataset average baseline.",
        )
        title = "Units Produced"

        insight = synthesize_conclusion_insight(
            title,
            [finding],
            ASSESSMENT_REQUIRES_MONITORING,
        )

        assert insight == (
            "Units Produced remains slightly below its historical baseline "
            "and should continue to be monitored."
        )
        assert summarize_finding_evidence(finding) == (
            "Snapshot analysis found performance below baseline."
        )

    def test_priority_actions_render_humanised_executive_wording(self):
        action = PriorityAction(
            action_id="action-0",
            rank=1,
            urgency="Monitor",
            action="Review snapshot performance for attendance_rate against baseline.",
            rationale="Based on LOW severity snapshot finding(s) linked to attendance_rate.",
            linked_finding_ids=["finding-0"],
            linked_theme_ids=["theme-metric-attendance_rate"],
            linked_conclusion_ids=["conclusion-0"],
        )

        presentation = format_priority_action(action)

        assert presentation.header == "Priority 1 • Monitor"
        assert presentation.action_text == (
            "Review Attendance Rate against the historical baseline."
        )
        assert humanise_priority_action_text(action.action) == presentation.action_text
        assert presentation.reason_label == "Reason"
        assert presentation.reason_text == (
            "Lower-severity snapshot findings should continue to be monitored for emerging patterns."
        )
        assert "_" not in presentation.action_text

    def test_humanise_priority_rationale_leaves_unknown_patterns_unchanged(self):
        rationale = "Custom rationale text."

        assert humanise_priority_rationale(rationale) == rationale


class TestFollowUpInvestigationPresentation:
    def test_split_follow_up_investigations_shows_top_three_by_default(self):
        investigations = [f"Investigation {index}" for index in range(1, 6)]

        presentation = split_follow_up_investigations(investigations)

        assert len(presentation.visible) == DEFAULT_INVESTIGATION_LIMIT
        assert presentation.visible == [
            "Investigation 1",
            "Investigation 2",
            "Investigation 3",
        ]
        assert presentation.additional == ["Investigation 4", "Investigation 5"]
        assert presentation.expander_label == ADDITIONAL_INVESTIGATIONS_EXPANDER_LABEL

    def test_split_follow_up_investigations_has_no_expander_when_three_or_fewer(self):
        investigations = ["One", "Two", "Three"]

        presentation = split_follow_up_investigations(investigations)

        assert presentation.visible == investigations
        assert presentation.additional == []


class TestExecutiveReasoningPresentationIntegration:
    def test_executive_reasoning_heading_constant(self):
        assert EXECUTIVE_REASONING_HEADING == "Executive Reasoning"

    def test_analysis_service_builds_analysis_overview_from_routes_and_assessment(self):
        from tests.support.factories import manufacturing_bundle
        from ui.analysis_service import run_analysis

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        assert result.report is not None
        overview = format_analysis_overview(
            findings=result.findings,
            routes=result.routes,
            report=result.report,
        )

        assert overview.bullets
        assert overview.bullets[0].endswith("finding" if len(result.findings) == 1 else "findings")
        assert any("executed" in bullet for bullet in overview.bullets)
        assert overview.bullets[-1] in {
            "Low operational risk",
            "Moderate operational risk",
            "High operational risk",
        }

    def test_analysis_service_report_exposes_reasoning_fields(self):
        from tests.support.factories import manufacturing_bundle
        from ui.analysis_service import run_analysis

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        assert result.report is not None
        assert should_show_executive_reasoning(result.report)
        assert should_show_operational_assessment(result.report)
        assert should_show_executive_conclusions(result.report)
        assert should_show_priority_actions(result.report)
        assert should_show_recommended_actions(result.report) is False

        conclusion = format_executive_conclusion(
            result.report.executive_conclusions[0],
            result.report,
        )
        assert conclusion.insight
        assert conclusion.evidence_bullets
        assert result.report.executive_conclusions[0].evidence_summary[0] not in (
            conclusion.evidence_bullets
        )

    def test_legacy_report_generation_still_supports_recommended_actions(self):
        from src.operational_intelligence.reporting import ExecutiveReportGenerator
        from tests.support.builders import make_sample_findings

        report = ExecutiveReportGenerator().generate(make_sample_findings())

        assert should_show_executive_reasoning(report) is False
        assert should_show_operational_assessment(report) is False
        assert should_show_executive_conclusions(report) is False
        assert should_show_priority_actions(report) is False
        assert should_show_recommended_actions(report) is True
        assert report.executive_summary
        assert report.high_priority_findings

    def test_empty_findings_report_hides_reasoning_sections(self):
        from src.operational_intelligence.executive_reasoning import ExecutiveReasoningEngine
        from src.operational_intelligence.reporting import ExecutiveReportGenerator

        reasoning = ExecutiveReasoningEngine().reason([])
        report = ExecutiveReportGenerator().generate([], reasoning=reasoning)

        assert should_show_executive_reasoning(report) is True
        assert should_show_operational_assessment(report) is True
        assert report.operational_assessment is not None
        assert report.operational_assessment.assessment_level == "Healthy"
        assert should_show_executive_conclusions(report) is False
        assert should_show_priority_actions(report) is False
        assert should_show_recommended_actions(report) is False

    def test_sample_findings_investigations_split_into_visible_and_additional(self):
        from src.operational_intelligence.reporting import ExecutiveReportGenerator
        from tests.support.builders import make_sample_findings

        report = ExecutiveReportGenerator().generate(make_sample_findings())
        presentation = split_follow_up_investigations(
            report.suggested_follow_up_investigations
        )

        assert len(presentation.visible) <= DEFAULT_INVESTIGATION_LIMIT
        assert len(presentation.visible) + len(presentation.additional) == len(
            report.suggested_follow_up_investigations
        )
        if len(report.suggested_follow_up_investigations) > DEFAULT_INVESTIGATION_LIMIT:
            assert presentation.additional
