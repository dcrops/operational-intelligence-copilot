"""Deterministic formatters for System Transparency sections."""

from __future__ import annotations

from src.operational_intelligence.models import AnalysisRequest, Finding
from src.operational_intelligence.schema_resolution import resolve_metric_from_question

_TRANSPARENCY_METADATA_KEYS = frozenset(
    {
        "row_index",
        "mean",
        "standard_deviation",
        "z_score",
        "anomaly_direction",
        "aggregation",
        "comparison_direction",
        "comparison_extreme",
        "is_comparison_target",
        "trend_label",
        "n_periods",
        "pct_change",
        "pct_change_percent",
        "normalized_slope",
        "reversals",
        "positive_steps",
        "negative_steps",
        "cv",
        "range_ratio",
    }
)


def _looks_like_period_key(key: str, value: object) -> bool:
    key_lower = key.lower()
    if "date" in key_lower or key_lower.endswith("_at"):
        return True
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return True
    return False


def format_clarification_trail(request: AnalysisRequest) -> list[str]:
    """Return user clarification selections from the final analysis request."""
    lines: list[str] = []
    if request.selected_metrics:
        lines.append(f"Metric selected: {', '.join(request.selected_metrics)}")
    if request.selected_dimensions:
        lines.append(f"Dimension selected: {', '.join(request.selected_dimensions)}")
    if request.requested_analysis_type:
        lines.append(f"Analysis type selected: {request.requested_analysis_type}")
    if request.selected_comparison_direction:
        lines.append(
            f"Comparison direction selected: {request.selected_comparison_direction}"
        )
    if request.selected_date_column:
        lines.append(f"Date column selected: {request.selected_date_column}")
    return lines


def _collect_metric_names(findings: list[Finding]) -> list[str]:
    metrics: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for item in finding.evidence:
            if item.metric_name and item.metric_name not in seen:
                metrics.append(item.metric_name)
                seen.add(item.metric_name)
    return metrics


def resolve_metrics_analysed(
    request: AnalysisRequest,
    routes: list[str],
    available_metrics: list[str],
) -> list[str]:
    """Return metrics scanned during anomaly detection for transparency display."""
    if "anomaly_detection" not in routes:
        return []
    if request.selected_metrics:
        return list(request.selected_metrics)

    metric_col = resolve_metric_from_question(request.question, available_metrics)
    if metric_col is not None:
        return [metric_col]
    return list(available_metrics)


def _is_multi_metric_anomaly_analysis(
    request: AnalysisRequest,
    routes: list[str],
    metrics_analysed: list[str],
) -> bool:
    if request.selected_metrics:
        return False
    if "anomaly_detection" not in routes:
        return False
    return len(metrics_analysed) > 1


def format_metrics_analysed_trail(metrics_analysed: list[str]) -> list[str]:
    """Return metrics analysed across the run (multi-metric anomaly scans)."""
    if len(metrics_analysed) > 1:
        return list(metrics_analysed)
    return []


def _first_aggregation(findings: list[Finding]) -> str | None:
    for finding in findings:
        for item in finding.evidence:
            aggregation = item.supporting_context.get("aggregation")
            if aggregation is not None:
                return str(aggregation)
    return None


def _first_comparison_direction(findings: list[Finding]) -> str | None:
    for finding in findings:
        if "variance" not in finding.title.lower():
            continue
        for item in finding.evidence:
            direction = item.supporting_context.get("comparison_direction")
            if direction is not None:
                return str(direction)
    return None


def _first_dimension_column(findings: list[Finding], routes: list[str]) -> str | None:
    if "variance_analysis" not in routes:
        return None

    for finding in findings:
        if "variance" not in finding.title.lower():
            continue
        for item in finding.evidence:
            for key, value in item.supporting_context.items():
                if key in _TRANSPARENCY_METADATA_KEYS or value is None:
                    continue
                if isinstance(value, bool):
                    continue
                if isinstance(value, (int, float)):
                    continue
                if _looks_like_period_key(key, value):
                    continue
                return key
    return None


def format_auto_resolved_trail(
    request: AnalysisRequest,
    findings: list[Finding],
    routes: list[str],
    *,
    metrics_analysed: list[str] | None = None,
) -> list[str]:
    """Return automatically inferred analytical decisions visible in findings."""
    if not findings:
        return []

    lines: list[str] = []
    analysed = metrics_analysed or []
    multi_metric_anomaly = _is_multi_metric_anomaly_analysis(request, routes, analysed)

    if not request.selected_metrics and not multi_metric_anomaly:
        metrics = _collect_metric_names(findings)
        if len(metrics) == 1:
            lines.append(f"Metric inferred: {metrics[0]}")

    if not request.selected_dimensions:
        dimension = _first_dimension_column(findings, routes)
        if dimension:
            lines.append(f"Dimension inferred: {dimension}")

    aggregation = _first_aggregation(findings)
    if aggregation:
        lines.append(f"Aggregation inferred: {aggregation}")

    if not request.selected_comparison_direction and "variance_analysis" in routes:
        comparison_direction = _first_comparison_direction(findings)
        if comparison_direction:
            lines.append(f"Comparison direction inferred: {comparison_direction}")

    return lines
