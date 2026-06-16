"""
Full-pipeline behavioural scenarios across manufacturing, education, and workforce.

Uses synthetic factories and shared assertion helpers; no sample CSV dependency.
"""

from __future__ import annotations

import pytest

from src.operational_intelligence.answer_generator import AnswerGenerator
from ui.analysis_service import run_analysis
from ui.anomaly_presentation import anomaly_business_description, anomaly_direction_label
from tests.support.assertions import (
    assert_clarification,
    assert_no_clarification,
    assert_run_analysis_complete,
    assert_trend_outcome,
    assert_variance_outcome,
)
from tests.support.factories import (
    MANUFACTURING_HIGHEST_DEFECTS_LINE,
    MANUFACTURING_LOWEST_DEFECTS_LINE,
    EDUCATION_LOWEST_ATTENDANCE_SCHOOL,
    WORKFORCE_HIGHEST_HOURS_DEPARTMENT,
    WORKFORCE_LOWEST_HOURS_DEPARTMENT,
    education_bundle,
    manufacturing_bundle,
    workforce_bundle,
)


def _anomaly_findings(findings):
    return [finding for finding in findings if "anomaly" in finding.title.lower()]


def _trend_period_values(findings):
    finding = next(f for f in findings if "trend" in f.title.lower())
    return [
        item.metric_value
        for item in finding.evidence
        if item.metric_value is not None
        and "Trend classification" not in item.description
    ]


@pytest.mark.integration
class TestManufacturingPipelineScenarios:
    def test_trend_downtime_minutes_runs_without_clarification(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has downtime_minutes changed over time?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["trend_analysis"]
        assert_run_analysis_complete(result)
        assert_trend_outcome(
            result.findings,
            expected_metric="downtime_minutes",
            expected_aggregation="sum",
        )

    def test_variance_highest_defects_by_production_line(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["variance_analysis"]
        assert_run_analysis_complete(result)
        assert_variance_outcome(
            result.findings,
            expected_metric="defects",
            expected_dimension="production_line",
            expected_aggregation="sum",
            expected_direction="top",
            expected_targets=[MANUFACTURING_HIGHEST_DEFECTS_LINE],
        )

    def test_variance_lowest_defects_by_production_line(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the lowest defects?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["variance_analysis"]
        assert_variance_outcome(
            result.findings,
            expected_metric="defects",
            expected_dimension="production_line",
            expected_aggregation="sum",
            expected_direction="bottom",
            expected_targets=[MANUFACTURING_LOWEST_DEFECTS_LINE],
        )

    def test_performance_question_requires_metric_clarification(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has performance changed over time?",
            df,
            profile,
        )

        assert_clarification(
            result,
            "metric",
            options=["defects", "downtime_minutes", "units_produced"],
        )
        assert result.routes == ["trend_analysis"]


@pytest.mark.integration
class TestEducationPipelineScenarios:
    def test_trend_attendance_uses_mean_and_realistic_values(self):
        df, profile = education_bundle()
        result = run_analysis(
            "How has attendance changed over time?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["trend_analysis"]
        assert_run_analysis_complete(result)
        assert_trend_outcome(
            result.findings,
            expected_metric="attendance_rate",
            expected_aggregation="mean",
        )
        values = _trend_period_values(result.findings)
        assert values
        assert all(0 <= value <= 100 for value in values)

    def test_variance_lowest_attendance_by_school(self):
        df, profile = education_bundle()
        result = run_analysis(
            "Which school has the lowest attendance?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["variance_analysis"]
        assert_variance_outcome(
            result.findings,
            expected_metric="attendance_rate",
            expected_dimension="school",
            expected_aggregation="mean",
            expected_direction="bottom",
            expected_targets=[EDUCATION_LOWEST_ATTENDANCE_SCHOOL],
        )

    def test_best_class_routes_to_variance_and_requests_metric_clarification(self):
        df, profile = education_bundle()
        result = run_analysis(
            "Which class is performing best?",
            df,
            profile,
        )

        assert result.routes == ["variance_analysis"]
        assert "anomaly_detection" not in result.routes
        assert_clarification(result, "metric")
        assert result.findings == []

    def test_performance_question_requires_metric_clarification(self):
        df, profile = education_bundle()
        result = run_analysis(
            "How has performance changed?",
            df,
            profile,
        )

        assert_clarification(result, "metric")
        assert set(result.clarification.options) == {
            "attendance_rate",
            "behaviour_incidents",
            "average_score",
        }


@pytest.mark.integration
class TestWorkforcePipelineScenarios:
    def test_variance_lowest_hours_by_department(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "Which department has the lowest hours?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["variance_analysis"]
        assert_variance_outcome(
            result.findings,
            expected_metric="hours",
            expected_dimension="department",
            expected_aggregation="sum",
            expected_direction="bottom",
            expected_targets=[WORKFORCE_LOWEST_HOURS_DEPARTMENT],
        )

    def test_variance_dual_best_and_worst_hours(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "Which department has the best and worst hours?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["variance_analysis"]
        assert_variance_outcome(
            result.findings,
            expected_metric="hours",
            expected_dimension="department",
            expected_aggregation="sum",
            expected_direction="dual",
            expected_targets=[
                WORKFORCE_HIGHEST_HOURS_DEPARTMENT,
                WORKFORCE_LOWEST_HOURS_DEPARTMENT,
            ],
        )
        targets = [
            item
            for finding in result.findings
            if "variance" in finding.title.lower()
            for item in finding.evidence
            if item.supporting_context.get("is_comparison_target")
        ]
        extremes = {item.supporting_context.get("comparison_extreme") for item in targets}
        assert extremes == {"top", "bottom"}

    def test_anomaly_direction_matches_direct_answer_and_business_copy(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "What looks unusual?",
            df,
            profile,
        )

        assert_no_clarification(result)
        assert result.routes == ["anomaly_detection"]
        anomaly_findings = _anomaly_findings(result.findings)
        assert anomaly_findings

        finding = anomaly_findings[0]
        assert finding.evidence
        direction = finding.evidence[0].supporting_context.get("anomaly_direction")
        assert direction in {"HIGH", "LOW"}

        answer_generator = AnswerGenerator()
        direct_answer = answer_generator._direct_anomaly_answer(finding)
        business_copy = anomaly_business_description(
            finding,
            finding.evidence[0].metric_name.replace("_", " "),
        )
        label = anomaly_direction_label(finding)

        assert direct_answer is not None
        assert direction in direct_answer
        assert label in {"high", "low", "mixed"}
        if label == "high":
            assert "high value" in business_copy
        elif label == "low":
            assert "low value" in business_copy

    def test_performance_question_requires_metric_clarification(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "How has performance changed?",
            df,
            profile,
        )

        assert_clarification(result, "metric")
        assert set(result.clarification.options) == {
            "hours",
            "overtime_hours",
            "absence_days",
        }


@pytest.mark.integration
class TestMixedIntentClarification:
    def test_unusual_and_highest_hours_requires_analysis_type_choice(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "What looks unusual and which department has the highest hours?",
            df,
            profile,
        )

        assert result.findings == []
        assert result.report is None
        assert result.direct_answer == ""
        assert set(result.routes) == {"variance_analysis", "anomaly_detection"}
        assert_clarification(
            result,
            "analysis_type",
            options=["variance_analysis", "anomaly_detection"],
        )

    @pytest.mark.parametrize(
        ("requested_analysis_type", "expected_route_subset"),
        [
            ("variance_analysis", ["variance_analysis"]),
            ("anomaly_detection", ["anomaly_detection"]),
        ],
    )
    def test_analysis_type_selection_runs_chosen_tool_only(
        self,
        requested_analysis_type,
        expected_route_subset,
    ):
        df, profile = workforce_bundle()
        question = "What looks unusual and which department has the highest hours?"
        result = run_analysis(
            question,
            df,
            profile,
            requested_analysis_type=requested_analysis_type,
        )

        assert_no_clarification(result)
        assert result.routes == expected_route_subset
