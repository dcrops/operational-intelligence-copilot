"""Deterministic Direct Answer formatting for snapshot findings."""

from __future__ import annotations

from src.operational_intelligence.models import EvidenceItem, Finding
from src.operational_intelligence.snapshot_analysis import extract_snapshot_contributors


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

    answer = (
        f"{metric_label} in {period_label} was {_format_number(period_value)}"
    )

    baseline_item = _baseline_item(finding.evidence)
    if baseline_item is None or not isinstance(baseline_item.metric_value, (int, float)):
        base_answer = f"{answer}."
    else:
        baseline_value = float(baseline_item.metric_value)
        answer = (
            f"{answer}, compared with a dataset average of "
            f"{_format_number(baseline_value)}"
        )

        delta = baseline_item.supporting_context.get("delta_vs_baseline")
        if isinstance(delta, (int, float)) and float(delta) != 0:
            delta_value = float(delta)
            delta_text = _format_number(abs(delta_value))
            if delta_value > 0:
                base_answer = f"{answer} (+{delta_text} above baseline)."
            else:
                base_answer = f"{answer} (-{delta_text} below baseline)."
        else:
            base_answer = f"{answer}."

    contributors = extract_snapshot_contributors(finding)
    if contributors is None:
        return base_answer

    _, highest, lowest = contributors
    return (
        f"{base_answer}\n\n"
        f"{_format_contributor_line('Highest contributor', highest.entity_name, float(highest.value))}\n\n"
        f"{_format_contributor_line('Lowest contributor', lowest.entity_name, float(lowest.value))}"
    )
