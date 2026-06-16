"""
Cross-dataset regression tests for comparative direction, aggregation, routing, and ambiguity.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.profiling import DatasetProfiler
from tests.support.assertions import assert_clarification, assert_variance_outcome
from tests.support.factories import (
    EDUCATION_LOWEST_ATTENDANCE_SCHOOL,
    WORKFORCE_LOWEST_HOURS_DEPARTMENT,
    education_bundle,
    workforce_bundle,
)
from ui.variance_presentation import variance_business_description


def _profile(name: str, path: str):
    df = pd.read_csv(path)
    return df, DatasetProfiler().profile_dataframe(name, df)


def _variance_finding(findings):
    return next(f for f in findings if "variance" in f.title.lower())


def _variance_target_evidence(finding):
    return [
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target") is True
    ]


def _trend_period_evidence(finding):
    return [
        item
        for item in finding.evidence
        if item.metric_value is not None
        and "Trend classification" not in item.description
    ]


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
def test_performance_questions_require_metric_clarification(
    dataset_name,
    path,
    question,
):
    df, profile = _profile(dataset_name, path)
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
    assert isinstance(findings, list)
    assert_variance_outcome(
        findings,
        expected_metric="attendance_rate",
        expected_dimension="school",
        expected_aggregation="mean",
        expected_direction="bottom",
        expected_targets=[EDUCATION_LOWEST_ATTENDANCE_SCHOOL],
    )

    finding = _variance_finding(findings)
    answer = AnswerGenerator()._direct_variance_answer(finding)
    business = variance_business_description(finding, "attendance rate")

    assert answer is not None
    assert EDUCATION_LOWEST_ATTENDANCE_SCHOOL in answer
    assert "lowest mean" in answer
    assert EDUCATION_LOWEST_ATTENDANCE_SCHOOL in business
    assert "lowest" in business


@pytest.mark.e2e
def test_education_attendance_trend_uses_mean_not_sum():
    df, profile = _profile("education_demo", "data/sample/education_demo.csv")
    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="How has attendance changed over time?",
            dataset_names=["education_demo"],
        ),
        df,
        [profile],
    )
    trend = next(f for f in findings if "trend" in f.title.lower())
    period_items = _trend_period_evidence(trend)
    assert period_items
    assert all(item.metric_name == "attendance_rate" for item in period_items)
    assert all(
        item.supporting_context.get("aggregation") == "mean"
        for item in period_items
    )
    values = [item.metric_value for item in period_items]
    assert max(values) <= 100


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


@pytest.mark.e2e
def test_manufacturing_dual_comparison_runs_without_direction_clarification():
    df, profile = _profile("manufacturing_demo", "data/sample/manufacturing_demo.csv")
    outcome = OperationalPipeline().run(
        AnalysisRequest(
            question="Which production line has the highest and lowest defects?",
            dataset_names=["manufacturing_demo"],
        ),
        df,
        [profile],
    )
    assert isinstance(outcome, list)
    finding = _variance_finding(outcome)
    targets = _variance_target_evidence(finding)
    assert len(targets) == 2

    extremes = {
        item.supporting_context.get("comparison_extreme")
        for item in targets
    }
    assert extremes == {"top", "bottom"}
    assert all(
        item.supporting_context.get("comparison_direction") == "dual"
        for item in targets
    )
    assert all(item.metric_name == "defects" for item in targets)

    answer = AnswerGenerator()._direct_variance_answer(finding)
    assert answer is not None
    assert "highest" in answer.lower()
    assert "lowest" in answer.lower()


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

    answer = AnswerGenerator()._direct_variance_answer(_variance_finding(findings))
    assert answer is not None
    assert WORKFORCE_LOWEST_HOURS_DEPARTMENT in answer
    assert "lowest total" in answer


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
