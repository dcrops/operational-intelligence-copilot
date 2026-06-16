"""
Regression tests for Milestone 5–6 pipeline and UI integration behaviours.

Unit-level schema, semantics, trend, and presentation tests live in dedicated files.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.schema_resolution import non_identifier_dimensions
from ui.analysis_service import run_analysis
from ui.anomaly_presentation import anomaly_business_description, anomaly_direction_label
from tests.support.assertions import assert_run_analysis_complete, assert_trend_outcome


def _trend_metric_names(findings) -> set[str]:
    names: set[str] = set()
    for finding in findings:
        if "trend" not in finding.title.lower():
            continue
        for item in finding.evidence:
            if item.metric_name:
                names.add(item.metric_name)
    return names


def _anomaly_findings(findings):
    return [finding for finding in findings if "anomaly" in finding.title.lower()]


def _variance_finding(findings):
    return next(f for f in findings if "variance" in f.title.lower())


def _variance_target_evidence(finding):
    return [
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target") is True
    ]


@pytest.mark.integration
class TestPipelineMetricAndDimensionResolution:
    def test_pipeline_trend_uses_resolved_metric_not_first_profile_metric(
        self,
        manufacturing_df,
        manufacturing_profile,
        manufacturing_trend_request,
    ):
        assert manufacturing_profile.potential_metrics[0] == "defects"

        findings = OperationalPipeline().run(
            manufacturing_trend_request,
            manufacturing_df,
            [manufacturing_profile],
        )

        assert isinstance(findings, list)
        assert _trend_metric_names(findings) == {"downtime_minutes"}

    def test_pipeline_variance_uses_question_resolved_dimension_and_metric(
        self,
        workforce_df,
        workforce_profile,
        workforce_variance_request,
    ):
        findings = OperationalPipeline().run(
            workforce_variance_request,
            workforce_df,
            [workforce_profile],
        )

        assert isinstance(findings, list)
        finding = _variance_finding(findings)
        targets = _variance_target_evidence(finding)
        assert targets, "Expected a comparison target in variance evidence"

        target = targets[0]
        assert target.metric_name == "hours"
        assert target.supporting_context.get("department") is not None
        assert target.supporting_context.get("comparison_direction") == "top"
        assert target.supporting_context.get("aggregation") == "sum"
        assert target.supporting_context.get("is_comparison_target") is True


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

    def test_clarification_dimension_options_exclude_identifiers(
        self,
        workforce_profile,
    ):
        request = AnalysisRequest(
            question="Which group has the highest values?",
            dataset_names=["workforce_demo_v2"],
            selected_metrics=["hours"],
        )
        clarification = detect_clarification(
            request,
            ["variance_analysis"],
            workforce_profile,
        )

        assert isinstance(clarification, ClarificationRequest)
        assert clarification.clarification_type == "dimension"
        assert "employee_id" not in clarification.options


@pytest.mark.integration
class TestMultiStepClarificationWorkflow:
    def test_multi_step_clarification_preserves_selections_and_completes_analysis(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        question = "How has performance been affected?"

        metric_step = run_analysis(question, manufacturing_df, manufacturing_profile)
        assert metric_step.clarification is not None
        assert metric_step.clarification.clarification_type == "metric"

        dimension_step = run_analysis(
            question,
            manufacturing_df,
            manufacturing_profile,
            selected_metrics=["downtime_minutes"],
        )
        assert dimension_step.clarification is not None
        assert dimension_step.clarification.clarification_type == "dimension"
        assert dimension_step.request.selected_metrics == ["downtime_minutes"]

        completed = run_analysis(
            question,
            manufacturing_df,
            manufacturing_profile,
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


@pytest.mark.e2e
class TestAnomalyDirectionConsistency:
    def test_end_to_end_anomaly_direction_matches_direct_answer_and_business_copy(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        result = run_analysis(
            "What looks unusual?",
            manufacturing_df,
            manufacturing_profile,
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
            assert "high values" in business_copy
            assert "low values" not in business_copy
        elif label == "low":
            assert "low values" in business_copy
