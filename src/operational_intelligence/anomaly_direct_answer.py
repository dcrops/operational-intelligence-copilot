"""Adaptive Direct Answer formatting for anomaly findings."""

from __future__ import annotations

from src.operational_intelligence.models import EvidenceItem, Finding

_MEDIUM_SAMPLE_SIZE = 3
_LARGE_THRESHOLD = 20
_SMALL_MAX = 5

_CONTEXT_METADATA_KEYS = frozenset(
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


def _format_anomaly_context_label(item: EvidenceItem) -> str:
    metric_name = item.metric_name
    context_values: list[str] = []

    for key, value in item.supporting_context.items():
        if key in _CONTEXT_METADATA_KEYS or value is None:
            continue
        if metric_name and key == metric_name:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            continue
        if _looks_like_period_key(key, value):
            continue
        context_values.append(str(value))

    if context_values:
        return " / ".join(context_values)

    row_index = item.supporting_context.get("row_index")
    if row_index is not None:
        return f"Row {row_index}"
    return "Record"


def _normalized_anomaly_direction(item: EvidenceItem) -> str | None:
    raw_direction = item.supporting_context.get("anomaly_direction")
    if raw_direction is None:
        return None

    normalized = str(raw_direction).upper()
    if normalized in {"HIGH", "LOW"}:
        return normalized
    return None


def _numeric_evidence_items(finding: Finding) -> list[EvidenceItem]:
    return [
        item
        for item in finding.evidence
        if isinstance(item.metric_value, (int, float))
    ]


def _header_direction(items: list[EvidenceItem], extreme_item: EvidenceItem) -> str | None:
    directions = [
        direction
        for item in items
        if (direction := _normalized_anomaly_direction(item)) is not None
    ]
    if not directions:
        return None

    unique_directions = set(directions)
    if len(unique_directions) == 1:
        return next(iter(unique_directions))

    return _normalized_anomaly_direction(extreme_item)


def _select_extreme_item(items: list[EvidenceItem], direction: str | None) -> EvidenceItem:
    if direction == "LOW":
        return min(items, key=lambda item: item.metric_value)
    return max(items, key=lambda item: item.metric_value)


def _format_metric_value(value: int | float) -> str:
    return f"{value:g}"


def _format_z_score(item: EvidenceItem) -> str | None:
    z_score = item.supporting_context.get("z_score")
    if isinstance(z_score, (int, float)):
        return f"{float(z_score):.2f}"
    return None

def _format_mean(value: float) -> str:
    """Format mean values for user-facing anomaly explanations."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_anomaly_record_line(item: EvidenceItem) -> str:
    label = _format_anomaly_context_label(item)
    metric_name = item.metric_name or "metric"
    metric_value = _format_metric_value(item.metric_value)  # type: ignore[arg-type]
    mean = item.supporting_context.get("mean")
    z_score = _format_z_score(item)

    if isinstance(mean, (int, float)):
        line = (
            f"- {label}: {metric_name} = {metric_value}, "
            f"compared with an average of {_format_mean(mean)}"
        )
        if z_score is not None:
            line += f" (z-score {z_score})"
        line += "."
        return line

    line = f"- {label}: {metric_name} = {metric_value}"
    if z_score is not None:
        line += f" (z-score {z_score})"
    return line


def _sort_for_display(items: list[EvidenceItem]) -> list[EvidenceItem]:
    indexed = list(enumerate(items))

    def sort_key(pair: tuple[int, EvidenceItem]) -> tuple[int, int]:
        index, item = pair
        row_index = item.supporting_context.get("row_index")
        if isinstance(row_index, int):
            return (0, row_index)
        return (1, index)

    return [item for _, item in sorted(indexed, key=sort_key)]


def _sample_key(item: EvidenceItem, direction: str | None) -> tuple[float, float, int]:
    z_score = item.supporting_context.get("z_score")
    abs_z = abs(float(z_score)) if isinstance(z_score, (int, float)) else 0.0
    metric_value = float(item.metric_value)  # type: ignore[arg-type]
    extremity = metric_value if direction != "LOW" else -metric_value
    row_index = item.supporting_context.get("row_index")
    row_sort = int(row_index) if isinstance(row_index, int) else 0
    return (-abs_z, -extremity, row_sort)


def _select_sample_items(
    items: list[EvidenceItem],
    direction: str | None,
    sample_size: int,
) -> list[EvidenceItem]:
    ranked = sorted(items, key=lambda item: _sample_key(item, direction))
    return ranked[:sample_size]


def _intro_line(count: int, direction: str | None, metric_name: str) -> str:
    if count == 1:
        if direction:
            return f"1 unusual {direction} value was detected for {metric_name}."
        return f"1 unusual value was detected for {metric_name}."

    if direction:
        return f"{count} unusual {direction} values were detected for {metric_name}."
    return f"{count} unusual values were detected for {metric_name}."


def _extreme_sentence(extreme_item: EvidenceItem, direction: str | None) -> str:
    extreme_value = _format_metric_value(extreme_item.metric_value)  # type: ignore[arg-type]
    if direction == "LOW":
        return f"The lowest observed value was {extreme_value}."
    return f"The most extreme value was {extreme_value}."


def _remainder_sentence(remaining: int) -> str:
    if remaining == 1:
        return "1 additional anomalous record was also identified."
    return f"{remaining} additional anomalous records were also identified."


def build_anomaly_direct_answer(finding: Finding) -> str | None:
    """Build a tiered Direct Answer for an anomaly finding."""
    numeric_items = _numeric_evidence_items(finding)
    if not numeric_items:
        return None

    count = len(numeric_items)
    metric_name = numeric_items[0].metric_name or "metric"
    initial_extreme = max(numeric_items, key=lambda item: item.metric_value)
    direction = _header_direction(numeric_items, initial_extreme)
    extreme_item = _select_extreme_item(numeric_items, direction)

    lines = [_intro_line(count, direction, metric_name)]

    if count <= _SMALL_MAX:
        lines.append("")
        lines.append("Affected records:")
        for item in _sort_for_display(numeric_items):
            lines.append(_format_anomaly_record_line(item))
        return "\n".join(lines)

    lines.append("")
    lines.append(_extreme_sentence(extreme_item, direction))

    if count <= _LARGE_THRESHOLD:
        sample_items = _select_sample_items(
            numeric_items,
            direction,
            _MEDIUM_SAMPLE_SIZE,
        )
        lines.append("")
        lines.append("Examples include:")
        for item in _sort_for_display(sample_items):
            lines.append(_format_anomaly_record_line(item))
        lines.append("")
        lines.append(_remainder_sentence(count - _MEDIUM_SAMPLE_SIZE))
        return "\n".join(lines)

    lines.append("")
    lines.append("See supporting evidence for the complete list of affected records.")
    return "\n".join(lines)
