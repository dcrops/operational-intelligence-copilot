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
    assert outcome.clarification_type == "metric"
    assert len(outcome.options) == len(profile.potential_metrics)


@pytest.mark.e2e
def test_education_lowest_attendance_returns_bottom_school():
    df, profile = _profile("education_demo", "data/sample/education_demo.csv")
    expected_school = (
        df.groupby("school")["attendance_rate"].mean().idxmin()
    )

    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="Which school has the lowest attendance?",
            dataset_names=["education_demo"],
        ),
        df,
        [profile],
    )
    assert isinstance(findings, list)
    finding = _variance_finding(findings)
    targets = _variance_target_evidence(finding)
    assert len(targets) == 1

    target = targets[0]
    assert target.metric_name == "attendance_rate"
    assert target.supporting_context.get("comparison_direction") == "bottom"
    assert target.supporting_context.get("aggregation") == "mean"
    assert target.supporting_context.get("school") == expected_school

    answer = AnswerGenerator()._direct_variance_answer(finding)
    business = variance_business_description(finding, "attendance rate")

    assert answer is not None
    assert expected_school in answer
    assert "lowest mean" in answer
    assert expected_school in business
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


@pytest.mark.e2e
def test_education_best_class_routes_variance_and_requests_clarification():
    df, profile = _profile("education_demo", "data/sample/education_demo.csv")
    request = AnalysisRequest(
        question="Which class is performing best?",
        dataset_names=["education_demo"],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis"]
    clarification = detect_clarification(request, routes, profile)
    assert isinstance(clarification, ClarificationRequest)
    assert clarification.clarification_type == "metric"


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


@pytest.mark.e2e
def test_workforce_lowest_hours():
    df, profile = _profile("workforce_demo_v2", "data/sample/workforce_demo_v2.csv")
    expected_department = df.groupby("department")["hours"].sum().idxmin()

    findings = OperationalPipeline().run(
        AnalysisRequest(
            question="Which department has the lowest hours?",
            dataset_names=["workforce_demo_v2"],
        ),
        df,
        [profile],
    )
    finding = _variance_finding(findings)
    targets = _variance_target_evidence(finding)
    assert len(targets) == 1

    target = targets[0]
    assert target.metric_name == "hours"
    assert target.supporting_context.get("department") == expected_department
    assert target.supporting_context.get("comparison_direction") == "bottom"
    assert target.supporting_context.get("aggregation") == "sum"

    answer = AnswerGenerator()._direct_variance_answer(finding)
    assert answer is not None
    assert expected_department in answer
    assert "lowest total" in answer


@pytest.mark.integration
def test_mixed_intent_returns_analysis_type_clarification():
    df, profile = _profile("workforce_demo_v2", "data/sample/workforce_demo_v2.csv")
    clarification = detect_clarification(
        AnalysisRequest(
            question="What looks unusual and which department has the highest hours?",
            dataset_names=["workforce_demo_v2"],
        ),
        ["variance_analysis", "anomaly_detection"],
        profile,
    )
    assert isinstance(clarification, ClarificationRequest)
    assert clarification.clarification_type == "analysis_type"
    assert clarification.options == ["variance_analysis", "anomaly_detection"]


@pytest.mark.e2e
def test_behaviour_incidents_is_available_as_metric():
    _, profile = _profile("education_demo", "data/sample/education_demo.csv")
    assert "behaviour_incidents" in profile.potential_metrics
