"""Deterministic Direct Answer formatting for snapshot findings."""

from __future__ import annotations

from src.operational_intelligence.models import EvidenceItem, Finding
from src.operational_intelligence.snapshot_analysis import extract_snapshot_contributors

# Absolute delta below this threshold is described as broadly in line with baseline.
SNAPSHOT_DELTA_IN_LINE_THRESHOLD = 0.1


def _format_metric_label(metric_name: str) -> str:
    label = metric_name.replace("_", " ").strip()
    if not label:
        return "Metric"
    return label[0].upper() + label[1:]


def _format_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_contributor_line(label: str, entity_name: str, value: float) -> str:
    return f"{label}:\n{entity_name} ({_format_number(value)})"


def _snapshot_value_item(evidence: list[EvidenceItem]) -> EvidenceItem | None:
    for item in evidence:
        if item.supporting_context.get("analysis_mode") != "snapshot":
            continue
        if item.description.startswith("Snapshot value for"):
            return item
    return None


def _baseline_item(evidence: list[EvidenceItem]) -> EvidenceItem | None:
    for item in evidence:
        if item.description == "Full-dataset baseline comparison.":
            return item
    return None


def _resolve_delta_vs_baseline(
    period_value: float,
    baseline_value: float,
    baseline_item: EvidenceItem,
) -> float:
    delta = baseline_item.supporting_context.get("delta_vs_baseline")
    if isinstance(delta, (int, float)):
        return float(delta)
    return period_value - baseline_value


def _is_delta_broadly_in_line(delta: float) -> bool:
    return abs(delta) < SNAPSHOT_DELTA_IN_LINE_THRESHOLD


def _format_baseline_comparison(
    metric_label: str,
    period_label: str,
    period_value: float,
    baseline_value: float,
    delta: float,
) -> str:
    period_text = (
        f"{metric_label} in {period_label} was {_format_number(period_value)}"
    )
    baseline_text = _format_number(baseline_value)

    if _is_delta_broadly_in_line(delta):
        return (
            f"{period_text}, broadly in line with the dataset average of "
            f"{baseline_text}."
        )

    delta_text = _format_number(abs(delta))
    if delta > 0:
        return (
            f"{period_text}, above the dataset average of {baseline_text} "
            f"(+{delta_text} above baseline)."
        )
    return (
        f"{period_text}, below the dataset average of {baseline_text} "
        f"(-{delta_text} below baseline)."
    )


def build_snapshot_direct_answer(finding: Finding) -> str | None:
    """Build a snapshot direct answer from finding evidence metadata."""
    if not finding.evidence:
        return None

    snapshot_item = _snapshot_value_item(finding.evidence)
    if snapshot_item is None:
        return None
    if not isinstance(snapshot_item.metric_value, (int, float)):
        return None

    period_label = str(
        snapshot_item.supporting_context.get("period_label") or "the period"
    )
    metric_name = snapshot_item.metric_name or "metric"
    metric_label = _format_metric_label(metric_name)
    period_value = float(snapshot_item.metric_value)

    baseline_item = _baseline_item(finding.evidence)
    if baseline_item is None or not isinstance(baseline_item.metric_value, (int, float)):
        base_answer = (
            f"{metric_label} in {period_label} was {_format_number(period_value)}."
        )
    else:
        baseline_value = float(baseline_item.metric_value)
        delta = _resolve_delta_vs_baseline(period_value, baseline_value, baseline_item)
        base_answer = _format_baseline_comparison(
            metric_label,
            period_label,
            period_value,
            baseline_value,
            delta,
        )

    contributors = extract_snapshot_contributors(finding)
    if contributors is None:
        return base_answer

    _, highest, lowest = contributors
    return (
        f"{base_answer}\n\n"
        f"{_format_contributor_line('Highest contributor', highest.entity_name, float(highest.value))}\n\n"
        f"{_format_contributor_line('Lowest contributor', lowest.entity_name, float(lowest.value))}"
    )
