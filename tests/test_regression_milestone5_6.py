"""
Regression tests for Milestone 5–6 pipeline and UI integration behaviours.

Unit-level schema, semantics, trend, and presentation tests live in dedicated files.
"""

from __future__ import annotations

import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.schema_resolution import non_identifier_dimensions
from ui.analysis_service import run_analysis
from ui.anomaly_presentation import anomaly_business_description, anomaly_direction_label
from tests.support.assertions import assert_run_analysis_complete, assert_trend_outcome, assert_variance_outcome
from tests.support.factories import (
    WORKFORCE_HIGHEST_HOURS_DEPARTMENT,
    manufacturing_bundle,
    workforce_bundle,
)


def _anomaly_findings(findings):
    return [finding for finding in findings if "anomaly" in finding.title.lower()]


@pytest.mark.integration
class TestPipelineMetricAndDimensionResolution:
    def test_pipeline_trend_uses_resolved_metric_not_first_profile_metric(
        self,
        manufacturing_trend_request,
    ):
        df, profile = manufacturing_bundle()
        assert profile.potential_metrics[0] == "defects"

        findings = OperationalPipeline().run(
            manufacturing_trend_request,
            df,
            [profile],
        )

        assert isinstance(findings, list)
        assert_trend_outcome(
            findings,
            expected_metric="downtime_minutes",
            expected_aggregation="sum",
        )

    def test_pipeline_variance_uses_question_resolved_dimension_and_metric(
        self,
        workforce_variance_request,
    ):
        df, profile = workforce_bundle()
        findings = OperationalPipeline().run(
            workforce_variance_request,
            df,
            [profile],
        )

        assert isinstance(findings, list)
        assert_variance_outcome(
            findings,
            expected_metric="hours",
            expected_dimension="department",
            expected_aggregation="sum",
            expected_direction="top",
            expected_targets=[WORKFORCE_HIGHEST_HOURS_DEPARTMENT],
        )


@pytest.mark.integration
class TestIdentifierExclusionInClarification:
    def test_non_identifier_dimensions_exclude_id_like_columns(self):
        workforce_dimensions = [
            "employee_id",
            "employee_name",
            "department",
            "location",
            "manager",
            "employment_type",
        ]
        filtered = non_identifier_dimensions(workforce_dimensions)
        assert "employee_id" not in filtered
        assert "department" in filtered

    def test_clarification_dimension_options_exclude_identifiers(self):
        _, profile = workforce_bundle()
        request = AnalysisRequest(
            question="Which group has the highest values?",
            dataset_names=[profile.dataset_name],
            selected_metrics=["hours"],
        )
        clarification = detect_clarification(
            request,
            ["variance_analysis"],
            profile,
        )

        assert isinstance(clarification, ClarificationRequest)
        assert clarification.clarification_type == "dimension"
        assert "employee_id" not in clarification.options


@pytest.mark.integration
class TestMultiStepClarificationWorkflow:
    def test_multi_step_clarification_preserves_selections_and_completes_analysis(self):
        df, profile = manufacturing_bundle()
        question = "How has performance been affected?"

        metric_step = run_analysis(question, df, profile)
        assert metric_step.clarification is not None
        assert metric_step.clarification.clarification_type == "metric"

        dimension_step = run_analysis(
            question,
            df,
            profile,
            selected_metrics=["downtime_minutes"],
        )
        assert dimension_step.clarification is not None
        assert dimension_step.clarification.clarification_type == "dimension"
        assert dimension_step.request.selected_metrics == ["downtime_minutes"]

        completed = run_analysis(
            question,
            df,
            profile,
            selected_metrics=["downtime_minutes"],
            selected_dimensions=["production_line"],
        )
        assert_run_analysis_complete(completed)
        assert "trend_analysis" in completed.routes
        assert_trend_outcome(
            completed.findings,
            expected_metric="downtime_minutes",
            expected_aggregation="sum",
        )


@pytest.mark.integration
class TestAnomalyDirectionConsistency:
    def test_anomaly_direction_matches_direct_answer_and_business_copy(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "What looks unusual?",
            df,
            profile,
        )
        assert result.clarification is None
        assert result.routes == ["anomaly_detection"]

        anomaly_findings = _anomaly_findings(result.findings)
        assert anomaly_findings, "Expected at least one anomaly finding"

        finding = next(
            f for f in anomaly_findings
            if f.evidence and f.evidence[0].supporting_context.get("anomaly_direction")
        )
        direction = finding.evidence[0].supporting_context["anomaly_direction"]
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
            assert "high values" in business_copy or "high value" in business_copy
            assert "low values" not in business_copy
        elif label == "low":
            assert "low values" in business_copy or "low value" in business_copy
