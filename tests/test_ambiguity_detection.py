import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.models import AnalysisRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from tests.support.assertions import (
    assert_clarification,
    assert_no_clarification,
    assert_trend_outcome,
    assert_variance_outcome,
)
from tests.support.factories import (
    MANUFACTURING_HIGHEST_DEFECTS_LINE,
    manufacturing_bundle,
    workforce_bundle,
)


@pytest.mark.integration
def test_trend_ambiguous_metric_requires_clarification():
    df, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="How has performance changed over time?",
        dataset_names=[profile.dataset_name],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert_clarification(
        outcome,
        "metric",
        options=list(profile.potential_metrics),
    )


@pytest.mark.integration
def test_trend_resolved_metric_runs_without_clarification():
    df, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="How has downtime changed over time?",
        dataset_names=[profile.dataset_name],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert_no_clarification(outcome)
    assert_trend_outcome(outcome, expected_metric="downtime_minutes", expected_aggregation="sum")


@pytest.mark.integration
def test_variance_resolved_dimension_and_metric_run_without_clarification():
    df, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="Which production line has the highest defects?",
        dataset_names=[profile.dataset_name],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert_no_clarification(outcome)
    assert_variance_outcome(
        outcome,
        expected_metric="defects",
        expected_dimension="production_line",
        expected_aggregation="sum",
        expected_direction="top",
        expected_targets=[MANUFACTURING_HIGHEST_DEFECTS_LINE],
    )


@pytest.mark.integration
def test_selected_metric_skips_clarification():
    df, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="How has performance changed over time?",
        dataset_names=[profile.dataset_name],
        selected_metrics=["downtime_minutes"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert_no_clarification(outcome)
    assert_trend_outcome(outcome, expected_metric="downtime_minutes", expected_aggregation="sum")


@pytest.mark.unit
def test_compare_question_requires_metric_clarification_first():
    _, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="Compare the schools.",
        dataset_names=[profile.dataset_name],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert_clarification(
        clarification,
        "metric",
        options=list(profile.potential_metrics),
    )


@pytest.mark.unit
def test_compare_question_with_resolved_metric_requests_dimension_clarification():
    _, profile = manufacturing_bundle()
    request = AnalysisRequest(
        question="Compare defects.",
        dataset_names=[profile.dataset_name],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert_clarification(
        clarification,
        "comparison_target",
        options=list(profile.potential_dimensions),
    )


@pytest.mark.unit
def test_variance_ambiguous_metric_requires_clarification_first():
    _, profile = workforce_bundle()
    request = AnalysisRequest(
        question="Which group has the highest values?",
        dataset_names=[profile.dataset_name],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert_clarification(clarification, "metric")
