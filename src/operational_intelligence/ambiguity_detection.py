"""Deterministic ambiguity detection before analytical tool execution."""

from __future__ import annotations

from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest, DatasetProfile
from src.operational_intelligence.question_semantics import (
    has_anomaly_intent,
    has_comparative_intent,
    has_conflicting_comparison_direction,
    question_uses_broad_metric_term,
    requests_dual_analysis_outcomes,
)
from src.operational_intelligence.schema_resolution import (
    has_explicit_column_mention,
    non_identifier_dimensions,
    resolve_dimension_from_question,
    resolve_metric_from_question,
)

_COMPARE_KEYWORDS = ("compare",)
_ANALYSIS_TYPE_OPTIONS = ["variance_analysis", "anomaly_detection"]


def is_compare_question(question: str) -> bool:
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in _COMPARE_KEYWORDS)


def detect_clarification(
    request: AnalysisRequest,
    tool_names: list[str],
    profile: DatasetProfile,
) -> ClarificationRequest | None:
    """
    Return a clarification request when schema resolution is ambiguous for routed tools.
    """
    metrics = list(profile.potential_metrics or [])
    dimensions = list(profile.potential_dimensions or [])
    comparison_dimensions = non_identifier_dimensions(dimensions) or dimensions

    mixed_intent = (
        has_comparative_intent(request.question)
        and has_anomaly_intent(request.question)
        and not requests_dual_analysis_outcomes(request.question)
    )
    if mixed_intent and not request.requested_analysis_type:
        return ClarificationRequest(
            clarification_type="analysis_type",
            message="I couldn't determine which analysis you want to run.",
            options=list(_ANALYSIS_TYPE_OPTIONS),
        )

    if has_conflicting_comparison_direction(request.question):
        return ClarificationRequest(
            clarification_type="comparison_direction",
            message="I couldn't determine whether you want the highest or lowest value.",
            options=["top", "bottom"],
        )

    for tool_name in tool_names:
        if tool_name == "risk_assessment":
            continue

        if tool_name == "trend_analysis":
            clarification = _trend_metric_clarification(request, metrics)
            if clarification is not None:
                return clarification

        if tool_name == "variance_analysis":
            clarification = _variance_metric_clarification(request, metrics)
            if clarification is not None:
                return clarification

            clarification = _variance_dimension_clarification(
                request,
                dimensions,
                comparison_dimensions,
            )
            if clarification is not None:
                return clarification

    return None


def _trend_metric_clarification(
    request: AnalysisRequest,
    metrics: list[str],
) -> ClarificationRequest | None:
    if request.selected_metrics:
        return None
    if resolve_metric_from_question(request.question, metrics) is not None:
        return None
    if len(metrics) <= 1:
        return None

    return ClarificationRequest(
        clarification_type="metric",
        message="I couldn't determine which metric you meant.",
        options=metrics,
    )


def _variance_metric_clarification(
    request: AnalysisRequest,
    metrics: list[str],
) -> ClarificationRequest | None:
    if request.selected_metrics:
        return None
    if resolve_metric_from_question(request.question, metrics) is not None:
        return None
    if len(metrics) <= 1:
        return None

    return ClarificationRequest(
        clarification_type="metric",
        message="I couldn't determine which metric you meant.",
        options=metrics,
    )


def _variance_dimension_clarification(
    request: AnalysisRequest,
    dimensions: list[str],
    comparison_dimensions: list[str],
) -> ClarificationRequest | None:
    if request.selected_dimensions:
        return None
    if resolve_dimension_from_question(request.question, dimensions) is not None:
        return None

    options = comparison_dimensions
    if len(options) <= 1:
        return None

    if is_compare_question(request.question):
        return ClarificationRequest(
            clarification_type="comparison_target",
            message="I couldn't determine what you want to compare.",
            options=options,
        )

    return ClarificationRequest(
        clarification_type="dimension",
        message="I couldn't determine which dimension you meant.",
        options=options,
    )


def needs_metric_clarification_for_broad_term(
    request: AnalysisRequest,
    metrics: list[str],
) -> bool:
    if request.selected_metrics:
        return False
    if not question_uses_broad_metric_term(request.question):
        return False
    if len(metrics) <= 1:
        return False
    return not any(
        has_explicit_column_mention(request.question, metric)
        for metric in metrics
    )
