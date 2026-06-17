"""
Cross-dataset regression tests for comparative direction, aggregation, routing, and ambiguity.

Sample CSV files are used only for the parametrized E2E smoke tests below.
"""

from __future__ import annotations

import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest, PipelineAnalysisResult
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.profiling import DatasetProfiler
from tests.support.assertions import assert_clarification, assert_trend_outcome, assert_variance_outcome, pipeline_findings
from tests.support.factories import (
    EDUCATION_LOWEST_ATTENDANCE_SCHOOL,
    MANUFACTURING_HIGHEST_DEFECTS_LINE,
    MANUFACTURING_LOWEST_DEFECTS_LINE,
    WORKFORCE_LOWEST_HOURS_DEPARTMENT,
    education_bundle,
    manufacturing_bundle,
    workforce_bundle,
)


def _load_csv_profile(name: str, path: str):
    import pandas as pd

    df = pd.read_csv(path)
    return df, DatasetProfiler().profile_dataframe(name, df)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("dataset_name", "path", "question"),
    [
        (
            "manufacturing_demo",
            "data/sample/manufacturing_demo.csv",
            "How has performance changed over time?",
        ),
        (
            "education_demo",
            "data/sample/education_demo.csv",
            "How has performance changed?",
        ),
        (
            "workforce_demo_v2",
            "data/sample/workforce_demo_v2.csv",
            "How has performance changed?",
        ),
    ],
)
def test_sample_csv_performance_questions_require_metric_clarification(
    dataset_name,
    path,
    question,
):
    df, profile = _load_csv_profile(dataset_name, path)
    outcome = OperationalPipeline().run(
        AnalysisRequest(question=question, dataset_names=[dataset_name]),
        df,
        [profile],
    )
    assert isinstance(outcome, ClarificationRequest)
    assert_clarification(outcome, "metric")
    assert len(outcome.options) == len(profile.potential_metrics)


@pytest.mark.integration
def test_education_lowest_attendance_returns_bottom_school():
    df, profile = education_bundle()

    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="Which school has the lowest attendance?",
            dataset_names=[profile.dataset_name],
        ),
        df,
        [profile],
    )
    assert isinstance(findings, PipelineAnalysisResult)
    assert_variance_outcome(
        findings,
        expected_metric="attendance_rate",
        expected_dimension="school",
        expected_aggregation="mean",
        expected_direction="bottom",
        expected_targets=[EDUCATION_LOWEST_ATTENDANCE_SCHOOL],
    )


@pytest.mark.integration
def test_education_attendance_trend_uses_mean_not_sum():
    df, profile = education_bundle()
    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="How has attendance changed over time?",
            dataset_names=[profile.dataset_name],
        ),
        df,
        [profile],
    )
    assert_trend_outcome(
        findings,
        expected_metric="attendance_rate",
        expected_aggregation="mean",
    )
    period_values = [
        item.metric_value
        for finding in pipeline_findings(findings)
        if "trend" in finding.title.lower()
        for item in finding.evidence
        if item.metric_value is not None
        and "Trend classification" not in item.description
    ]
    assert period_values
    assert all(0 <= value <= 100 for value in period_values)


@pytest.mark.integration
def test_education_best_class_routes_variance_and_requests_clarification():
    _, profile = education_bundle()
    request = AnalysisRequest(
        question="Which class is performing best?",
        dataset_names=[profile.dataset_name],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis"]
    clarification = detect_clarification(request, routes, profile)
    assert_clarification(clarification, "metric")


@pytest.mark.integration
def test_manufacturing_dual_comparison_runs_without_direction_clarification():
    df, profile = manufacturing_bundle()
    outcome = OperationalPipeline().run(
        AnalysisRequest(
            question="Which production line has the highest and lowest defects?",
            dataset_names=[profile.dataset_name],
        ),
        df,
        [profile],
    )
    assert isinstance(outcome, PipelineAnalysisResult)
    assert_variance_outcome(
        outcome,
        expected_metric="defects",
        expected_dimension="production_line",
        expected_aggregation="sum",
        expected_direction="dual",
        expected_targets=[
            MANUFACTURING_HIGHEST_DEFECTS_LINE,
            MANUFACTURING_LOWEST_DEFECTS_LINE,
        ],
    )


@pytest.mark.integration
def test_workforce_lowest_hours():
    df, profile = workforce_bundle()

    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="Which department has the lowest hours?",
            dataset_names=[profile.dataset_name],
        ),
        df,
        [profile],
    )
    assert_variance_outcome(
        findings,
        expected_metric="hours",
        expected_dimension="department",
        expected_aggregation="sum",
        expected_direction="bottom",
        expected_targets=[WORKFORCE_LOWEST_HOURS_DEPARTMENT],
    )


@pytest.mark.integration
def test_mixed_intent_returns_analysis_type_clarification():
    _, profile = workforce_bundle()
    clarification = detect_clarification(
        AnalysisRequest(
            question="What looks unusual and which department has the highest hours?",
            dataset_names=[profile.dataset_name],
        ),
        ["variance_analysis", "anomaly_detection"],
        profile,
    )
    assert_clarification(
        clarification,
        "analysis_type",
        options=["variance_analysis", "anomaly_detection"],
    )


@pytest.mark.unit
def test_behaviour_incidents_is_available_as_metric():
    _, profile = education_bundle()
    assert "behaviour_incidents" in profile.potential_metrics
