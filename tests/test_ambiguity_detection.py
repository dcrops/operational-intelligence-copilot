import pandas as pd

from src.operational_intelligence.ambiguity_detection import detect_clarification, is_compare_question
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.profiling import DatasetProfiler


MANUFACTURING_METRICS = ["defects", "downtime_minutes", "units_produced"]
MANUFACTURING_DIMENSIONS = ["production_line", "shift", "site", "supervisor"]


def _manufacturing_profile() -> tuple[pd.DataFrame, object]:
    df = pd.read_csv("data/sample/manufacturing_demo.csv")
    profile = DatasetProfiler().profile_dataframe("manufacturing_demo", df)
    return df, profile


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


def test_trend_resolved_metric_runs_without_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="How has downtime changed over time?",
        dataset_names=["manufacturing_demo"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    assert any("downtime_minutes" in finding.description for finding in outcome)


def test_variance_resolved_dimension_and_metric_run_without_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="Which production line has the highest defects?",
        dataset_names=["manufacturing_demo"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    assert outcome


def test_selected_metric_skips_clarification():
    df, profile = _manufacturing_profile()
    request = AnalysisRequest(
        question="How has performance changed over time?",
        dataset_names=["manufacturing_demo"],
        selected_metrics=["downtime_minutes"],
    )
    outcome = OperationalPipeline().run(request, df, [profile])

    assert not isinstance(outcome, ClarificationRequest)
    assert any("downtime_minutes" in finding.description for finding in outcome)


def test_compare_question_requires_dimension_clarification():
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
    assert clarification.clarification_type == "comparison_target"
    assert clarification.options == MANUFACTURING_DIMENSIONS


def test_variance_ambiguous_dimension_requires_clarification():
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
    assert clarification.clarification_type == "dimension"
    assert "employee_id" not in clarification.options


def test_is_compare_question():
    assert is_compare_question("Compare the schools.")
    assert not is_compare_question("Which production line has the highest defects?")


def test_multi_step_clarification_preserves_selected_metric():
    from ui.analysis_service import run_analysis

    df, profile = _manufacturing_profile()
    question = "How has performance been affected?"

    metric_clarification = run_analysis(question, df, profile)
    assert metric_clarification.clarification is not None
    assert metric_clarification.clarification.clarification_type == "metric"

    dimension_clarification = run_analysis(
        question,
        df,
        profile,
        selected_metrics=["downtime_minutes"],
    )
    assert dimension_clarification.clarification is not None
    assert dimension_clarification.clarification.clarification_type == "dimension"
    assert dimension_clarification.request.selected_metrics == ["downtime_minutes"]

    completed = run_analysis(
        question,
        df,
        profile,
        selected_metrics=["downtime_minutes"],
        selected_dimensions=["production_line"],
    )
    assert completed.clarification is None
    assert completed.findings
