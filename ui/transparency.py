"""Deterministic formatters for System Transparency sections."""

from __future__ import annotations

from src.operational_intelligence.models import AnalysisRequest, Finding, SnapshotContext, TemporalFilterContext
from src.operational_intelligence.schema_resolution import resolve_metric_from_question
from src.operational_intelligence.snapshot_analysis import extract_snapshot_contributors
from ui.metric_presentation import humanise_metric_name

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
        labels = ", ".join(humanise_metric_name(metric) for metric in request.selected_metrics)
        lines.append(f"Metric selected: {labels}")
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


def format_temporal_filter_trail(
    temporal_filter: TemporalFilterContext | None,
) -> list[str]:
    """Return temporal filtering metadata for System Transparency."""
    if temporal_filter is None:
        return []

    lines = [
        f"Period: {temporal_filter.label}",
        f"Date column: {temporal_filter.date_column}",
        (
            "Records analysed: "
            f"{temporal_filter.filtered_row_count} of {temporal_filter.original_row_count}"
        ),
    ]
    if temporal_filter.date_column_inferred:
        lines.append(f"Date column inferred: {temporal_filter.date_column}")
    return lines


def format_snapshot_trail(snapshot_context: SnapshotContext | None) -> list[str]:
    """Return snapshot mode metadata for System Transparency."""
    if snapshot_context is None or not snapshot_context.activated:
        return []

    return [
        f"Period: {snapshot_context.period_label}",
        f"Reason: {snapshot_context.reason}",
        "Analysis: Snapshot Intelligence",
    ]


def build_transparency_trail_lines(
    *,
    temporal_filter: TemporalFilterContext | None,
    snapshot_context: SnapshotContext | None,
    findings: list[Finding],
    request: AnalysisRequest,
    routes: list[str],
    metrics_analysed: list[str] | None = None,
) -> list[str]:
    """Assemble deterministic transparency lines for audit and narrative snapshot."""
    lines: list[str] = []
    lines.extend(format_temporal_filter_trail(temporal_filter))
    lines.extend(format_snapshot_trail(snapshot_context))
    lines.extend(format_snapshot_contributors_trail(findings))
    lines.extend(format_clarification_trail(request))
    lines.extend(
        format_auto_resolved_trail(
            request,
            findings,
            routes,
            metrics_analysed=metrics_analysed or [],
        )
    )
    lines.extend(format_metrics_analysed_trail(metrics_analysed or []))
    return lines


def format_snapshot_contributors_trail(findings: list[Finding]) -> list[str]:
    """Return snapshot contributor metadata for System Transparency."""
    for finding in findings:
        if "snapshot" not in finding.title.lower():
            continue
        contributors = extract_snapshot_contributors(finding)
        if contributors is None:
            continue

        dimension_name, highest, lowest = contributors
        return [
            f"Dimension: {dimension_name}",
            f"Highest: {highest.entity_name} ({_format_contributor_value(float(highest.value))})",
            f"Lowest: {lowest.entity_name} ({_format_contributor_value(float(lowest.value))})",
        ]
    return []


def _format_contributor_value(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


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
        return [humanise_metric_name(metric) for metric in metrics_analysed]
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
            lines.append(f"Metric inferred: {humanise_metric_name(metrics[0])}")

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
