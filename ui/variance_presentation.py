"""Variance finding presentation helpers for the UI."""

from src.operational_intelligence.models import Finding
from src.operational_intelligence.question_semantics import aggregation_label


def _target_evidence(finding: Finding):
    return [
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target") is True
    ]


def _context_dimension(ctx: dict) -> tuple[str | None, str | None]:
    ignored = {
        "aggregation",
        "comparison_direction",
        "comparison_extreme",
        "is_comparison_target",
    }
    for key, value in ctx.items():
        if key not in ignored and value is not None:
            return key, str(value)
    return None, None


def variance_business_description(finding: Finding, metric_label: str) -> str:
    if not finding.evidence:
        return (
            "Significant differences were observed across operational groups "
            "that may warrant operational review."
        )

    targets = _target_evidence(finding)
    if not targets:
        return (
            f"Significant differences were observed in {metric_label} across operational groups."
        )

    direction = targets[0].supporting_context.get("comparison_direction", "top")
    aggregation = targets[0].supporting_context.get("aggregation", "sum")
    agg_label = aggregation_label(str(aggregation))

    if direction == "dual" and len(targets) >= 2:
        top_item = next(
            (
                item
                for item in targets
                if item.supporting_context.get("comparison_extreme") == "top"
            ),
            targets[0],
        )
        bottom_item = next(
            (
                item
                for item in targets
                if item.supporting_context.get("comparison_extreme") == "bottom"
            ),
            targets[-1],
        )
        _, top_group = _context_dimension(top_item.supporting_context)
        _, bottom_group = _context_dimension(bottom_item.supporting_context)
        group_label = _context_dimension(top_item.supporting_context)[0] or "group"
        return (
            f"Significant differences were observed between {group_label}s, "
            f"with {top_group} recording the highest {agg_label} {metric_label} "
            f"and {bottom_group} recording the lowest {agg_label} {metric_label}."
        )

    item = targets[0]
    _, group = _context_dimension(item.supporting_context)
    group_label = _context_dimension(item.supporting_context)[0] or "group"
    direction_word = "highest" if direction == "top" else "lowest"

    if group:
        return (
            f"Significant differences were observed between {group_label}s, "
            f"with {group} recording the {direction_word} {agg_label} {metric_label}."
        )

    return (
        f"Significant differences were observed in {metric_label}, "
        f"with a {direction_word} {agg_label} value of {item.metric_value:g}."
    )
