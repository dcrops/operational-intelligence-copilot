"""Anomaly finding presentation helpers for the UI."""

from src.operational_intelligence.models import EvidenceItem, Finding


def _normalized_anomaly_direction(item: EvidenceItem) -> str | None:
    raw_direction = item.supporting_context.get("anomaly_direction")
    if raw_direction is None:
        return None

    normalized = str(raw_direction).upper()
    if normalized in {"HIGH", "LOW"}:
        return normalized
    return None


def anomaly_direction_label(finding: Finding) -> str | None:
    """
    Return a presentation label ('high' or 'low') from evidence anomaly_direction.
    """
    if not finding.evidence:
        return None

    directions = [
        direction
        for item in finding.evidence
        if (direction := _normalized_anomaly_direction(item)) is not None
    ]
    if not directions:
        return None

    unique_directions = set(directions)
    if len(unique_directions) == 1:
        return "high" if "HIGH" in unique_directions else "low"

    numeric_items = [
        item
        for item in finding.evidence
        if isinstance(item.metric_value, int | float)
    ]
    if not numeric_items:
        return None

    extreme_item = max(numeric_items, key=lambda item: item.metric_value)
    extreme_direction = _normalized_anomaly_direction(extreme_item)
    if extreme_direction == "HIGH":
        return "high"
    if extreme_direction == "LOW":
        return "low"

    return None


def anomaly_business_description(finding: Finding, metric_label: str) -> str:
    count = len(finding.evidence)

    if count == 0:
        return (
            "Unusual metric values were identified that differ significantly "
            "from normal operational patterns."
        )

    direction = anomaly_direction_label(finding)
    value_label = "value" if count == 1 else "values"

    if direction is None:
        return (
            f"{count} unusual {value_label} for {metric_label} were identified "
            "that differ significantly from normal operational patterns."
        )

    return (
        f"{count} unusually {direction} {value_label} for {metric_label} were identified "
        "that differ significantly from normal operational patterns."
    )
