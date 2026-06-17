import pandas as pd

from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import (
    AnalysisRequest,
    ClarificationRequest,
    DatasetProfile,
    PipelineAnalysisResult,
)
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from ui.models import AnalysisResult
from ui.transparency import resolve_metrics_analysed


def run_analysis(
    question: str,
    df: pd.DataFrame,
    profile: DatasetProfile,
    *,
    selected_metrics: list[str] | None = None,
    selected_dimensions: list[str] | None = None,
    selected_comparison_direction: str | None = None,
    selected_date_column: str | None = None,
    requested_analysis_type: str | None = None,
) -> AnalysisResult:
    """
    Run the operational intelligence flow for a natural language question.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Please enter a question before running analysis.")

    request = AnalysisRequest(
        question=cleaned_question,
        dataset_names=[profile.dataset_name],
        selected_metrics=selected_metrics or [],
        selected_dimensions=selected_dimensions or [],
        selected_comparison_direction=selected_comparison_direction,
        selected_date_column=selected_date_column,
        requested_analysis_type=requested_analysis_type,
    )

    routes = IntentRouter().route(request, [profile])
    pipeline_outcome = OperationalPipeline().run(request, df, [profile])

    if isinstance(pipeline_outcome, ClarificationRequest):
        return AnalysisResult(
            request=request,
            routes=routes,
            findings=[],
            report=None,
            direct_answer="",
            deterministic_answer="",
            clarification=pipeline_outcome,
            metrics_analysed=[],
            temporal_filter=None,
            snapshot_context=None,
        )

    findings = pipeline_outcome.findings
    temporal_filter = pipeline_outcome.temporal_filter
    snapshot_context = pipeline_outcome.snapshot_context
    metrics_analysed = resolve_metrics_analysed(
        request,
        routes,
        profile.potential_metrics,
    )
    report = ExecutiveReportGenerator().generate(findings)

    answer_generator = AnswerGenerator()
    deterministic_answer = answer_generator.generate(request, findings, report)
    if not findings:
        direct_answer = deterministic_answer
    else:
        direct_answer = answer_generator._build_direct_answer(
            request=request,
            findings=findings,
            report=report,
        )

    return AnalysisResult(
        request=request,
        routes=routes,
        findings=findings,
        report=report,
        direct_answer=direct_answer,
        deterministic_answer=deterministic_answer,
        metrics_analysed=metrics_analysed,
        temporal_filter=temporal_filter,
        snapshot_context=snapshot_context,
    )
