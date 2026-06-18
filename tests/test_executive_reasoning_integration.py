"""Integration tests for executive reasoning in the analysis service (Milestone 9f)."""

from __future__ import annotations

import pytest

from src.operational_intelligence.operational_assessment import ASSESSMENT_CRITICAL
from tests.support.assertions import assert_run_analysis_complete
from tests.support.factories import manufacturing_bundle
from ui.analysis_service import run_analysis


@pytest.mark.integration
class TestExecutiveReasoningIntegration:
    def test_analysis_service_populates_report_reasoning_fields(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        assert_run_analysis_complete(result)
        assert result.report is not None
        assert result.report.operational_assessment is not None
        assert result.report.executive_themes
        assert result.report.executive_conclusions
        assert result.report.priority_actions

    def test_analysis_service_recommended_next_steps_follow_priority_actions(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        assert result.report is not None
        assert result.report.priority_actions
        assert result.report.recommended_next_steps == [
            action.action for action in result.report.priority_actions
        ]

    def test_analysis_service_direct_answer_remains_unchanged(self):
        df, profile = manufacturing_bundle()
        question = "Which production line has the highest defects and what is the risk?"

        result = run_analysis(question, df, profile)

        assert result.direct_answer
        assert "Direct Answer:" not in result.direct_answer
        assert "production line" in result.direct_answer.lower() or "defects" in result.direct_answer.lower()

    def test_analysis_service_empty_findings_path_has_healthy_assessment(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "What is the trend in downtime_minutes over time?",
            df,
            profile,
            selected_metrics=["downtime_minutes"],
            requested_analysis_type="trend",
        )

        if not result.findings:
            assert result.report is not None
            assert result.report.operational_assessment is not None
            assert result.report.operational_assessment.assessment_level == "Healthy"
            assert result.report.executive_themes == []
            assert result.report.priority_actions == []
            return

        assert result.report is not None
        assert result.report.operational_assessment is not None

    def test_analysis_service_critical_findings_produce_critical_assessment(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        if any(finding.severity == "HIGH" for finding in result.findings):
            assert result.report is not None
            assert result.report.operational_assessment is not None
            assert result.report.operational_assessment.assessment_level == ASSESSMENT_CRITICAL
