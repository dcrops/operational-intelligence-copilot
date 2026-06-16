import pandas as pd
import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.profiling import DatasetProfiler


MANUFACTURING_METRICS = ["defects", "downtime_minutes", "units_produced"]
MANUFACTURING_DIMENSIONS = ["production_line", "shift", "site", "supervisor"]


def _manufacturing_profile() -> tuple[pd.DataFrame, object]:
    df = pd.read_csv("data/sample/manufacturing_demo.csv")
    profile = DatasetProfiler().profile_dataframe("manufacturing_demo", df)
    return df, profile


def _trend_metric_names(findings) -> set[str]:
    names: set[str] = set()
    for finding in findings:
        if "trend" not in finding.title.lower():
            continue
        for item in finding.evidence:
            if item.metric_name:
                names.add(item.metric_name)
    return names


def _variance_finding(findings):
    return next(f for f in findings if "variance" in f.title.lower())


def _variance_target_evidence(finding):
    return [
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target") is True
    ]


@pytest.mark.integration
def test_trend_ambiguous_metric_requires_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="How has performance changed over time?",
        dataset_names=["manufacturing_demo"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert isinstance(outcome, ClarificationRequest)
    assert outcome.clarification_type == "metric"
    assert outcome.message == "I couldn't determine which metric you meant."
    assert outcome.options == MANUFACTURING_METRICS


@pytest.mark.integration
def test_trend_resolved_metric_runs_without_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="How has downtime changed over time?",
        dataset_names=["manufacturing_demo"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    assert _trend_metric_names(outcome) == {"downtime_minutes"}


@pytest.mark.integration
def test_variance_resolved_dimension_and_metric_run_without_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="Which production line has the highest defects?",
        dataset_names=["manufacturing_demo"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    finding = _variance_finding(outcome)
    targets = _variance_target_evidence(finding)
    assert targets

    target = targets[0]
    assert target.metric_name == "defects"
    assert target.supporting_context.get("production_line") is not None
    assert target.supporting_context.get("comparison_direction") == "top"
    assert target.supporting_context.get("aggregation") == "sum"


@pytest.mark.integration
def test_selected_metric_skips_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="How has performance changed over time?",
        dataset_names=["manufacturing_demo"],
        selected_metrics=["downtime_minutes"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    assert _trend_metric_names(outcome) == {"downtime_minutes"}


@pytest.mark.unit
def test_compare_question_requires_metric_clarification_first():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="Compare the schools.",
        dataset_names=["manufacturing_demo"],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert isinstance(clarification, ClarificationRequest)
    assert clarification.clarification_type == "metric"
    assert clarification.options == MANUFACTURING_METRICS


@pytest.mark.unit
def test_compare_question_with_resolved_metric_requests_dimension_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="Compare defects.",
        dataset_names=["manufacturing_demo"],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert isinstance(clarification, ClarificationRequest)
    assert clarification.clarification_type == "comparison_target"
    assert clarification.options == MANUFACTURING_DIMENSIONS


@pytest.mark.unit
def test_variance_ambiguous_metric_requires_clarification_first():
    df = pd.read_csv("data/sample/workforce_demo_v2.csv")
    profile = DatasetProfiler().profile_dataframe("workforce_demo_v2", df)
    request = AnalysisRequest(
        question="Which group has the highest values?",
        dataset_names=["workforce_demo_v2"],
    )
    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert isinstance(clarification, ClarificationRequest)
    assert clarification.clarification_type == "metric"
