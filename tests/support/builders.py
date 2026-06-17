"""Synthetic Finding and Evidence builders for reporting/presentation tests."""

from __future__ import annotations

from src.operational_intelligence.models import EvidenceItem, Finding


def make_variance_evidence_item(
    *,
    dimension_key: str,
    dimension_value: str,
    metric_name: str,
    metric_value: float,
    aggregation: str,
    comparison_direction: str,
    is_comparison_target: bool = True,
    comparison_extreme: str | None = None,
) -> EvidenceItem:
    context: dict = {
        dimension_key: dimension_value,
        "aggregation": aggregation,
        "comparison_direction": comparison_direction,
        "is_comparison_target": is_comparison_target,
    }
    if comparison_extreme is not None:
        context["comparison_extreme"] = comparison_extreme

    return EvidenceItem(
        description=f"{dimension_key}={dimension_value}, {metric_name}={metric_value}",
        metric_name=metric_name,
        metric_value=metric_value,
        supporting_context=context,
    )


def make_variance_finding(
    evidence: list[EvidenceItem],
    *,
    severity: str = "MEDIUM",
) -> Finding:
    return Finding(
        title="Significant Variance Identified by Variance Analysis Tool",
        description="Variance across groups detected.",
        severity=severity,
        confidence="MEDIUM",
        evidence=evidence,
        recommended_action=(
            "Review discrepancies between highest and lowest categories to determine impact."
        ),
    )


def make_sample_findings() -> list[Finding]:
    """HIGH, MEDIUM, and LOW findings with distinct recommended actions."""
    return [
        Finding(
            title="Anomalies Detected by Anomaly Detection Tool",
            description="Anomalies were detected.",
            severity="HIGH",
            confidence="HIGH",
            evidence=[
                EvidenceItem(
                    description="Anomalous value",
                    metric_name="hours",
                    metric_value=900.0,
                    supporting_context={"anomaly_direction": "HIGH"},
                )
            ],
            recommended_action="Investigate the records identified as anomalous for potential operational issues.",
        ),
        Finding(
            title="Significant Variance Identified by Variance Analysis Tool",
            description="Variance across groups detected.",
            severity="MEDIUM",
            confidence="MEDIUM",
            evidence=[
                make_variance_evidence_item(
                    dimension_key="department",
                    dimension_value="Ops",
                    metric_name="hours",
                    metric_value=600.0,
                    aggregation="sum",
                    comparison_direction="top",
                )
            ],
            recommended_action="Review discrepancies between highest and lowest categories to determine impact.",
        ),
        Finding(
            title="Trend Identified by Trend Analysis Tool",
            description="The total hours increased from 100 to 220 (120.0% change). The series remained volatile.",
            severity="LOW",
            confidence="MEDIUM",
            evidence=[],
            recommended_action="Review the drivers for the observed trend to evaluate operational implications.",
        ),
    ]

def make_trend_finding(
    *,
    metric_name: str = "hours",
    trend_label: str | None = None,
    with_period_evidence: bool = True,
    with_group_metadata: bool = False,
    dimension_key: str = "department",
    dimension_value: str = "Ops",
) -> Finding:
    evidence: list[EvidenceItem] = []
    if with_period_evidence:
        evidence.append(
            EvidenceItem(
                description=f"period value for {metric_name}",
                metric_name=metric_name,
                metric_value=100.0,
                supporting_context={
                    "report_date": "2024-01-01",
                    "aggregation": "sum",
                },
            )
        )
    if with_group_metadata:
        evidence.append(
            EvidenceItem(
                description=f"group context for {metric_name}",
                metric_name=metric_name,
                metric_value=120.0,
                supporting_context={
                    dimension_key: dimension_value,
                    "aggregation": "sum",
                },
            )
        )
    context: dict = {"aggregation": "sum"}
    if trend_label is not None:
        context["trend_label"] = trend_label
    if trend_label is not None or with_period_evidence:
        evidence.append(
            EvidenceItem(
                description="Trend classification summary",
                metric_name=metric_name,
                supporting_context=context,
            )
        )

    return Finding(
        title="Trend Identified by Trend Analysis Tool",
        description=(
            f"The total {metric_name} increased from 100 to 220 (120.0% change). "
            "The series remained volatile over the period."
        ),
        severity="LOW",
        confidence="MEDIUM",
        evidence=evidence,
        recommended_action=(
            "Review the drivers for the observed trend to evaluate operational implications."
        ),
    )


def make_anomaly_evidence_item(
    *,
    metric_name: str = "defects",
    metric_value: float = 52.0,
    row_index: int | None = 126,
    z_score: float | None = 5.08,
    anomaly_direction: str = "HIGH",
    mean: float | None = None,
    standard_deviation: float | None = None,
    extra_context: dict | None = None,
) -> EvidenceItem:
    context: dict = {
        "anomaly_direction": anomaly_direction,
    }
    if row_index is not None:
        context["row_index"] = row_index
    if z_score is not None:
        context["z_score"] = z_score
    if mean is not None:
        context["mean"] = mean
    if standard_deviation is not None:
        context["standard_deviation"] = standard_deviation
    if extra_context:
        context.update(extra_context)

    return EvidenceItem(
        description="Anomalous value",
        metric_name=metric_name,
        metric_value=metric_value,
        supporting_context=context,
    )


def make_anomaly_evidence_items(
    count: int,
    *,
    metric_name: str = "defects",
    anomaly_direction: str = "HIGH",
    start_row_index: int = 126,
    start_metric_value: float = 52.0,
    start_z_score: float = 5.08,
    mean: float | None = None,
    standard_deviation: float | None = None,
    extra_context: dict | None = None,
) -> list[EvidenceItem]:
    return [
        make_anomaly_evidence_item(
            metric_name=metric_name,
            metric_value=start_metric_value + (index * 6),
            row_index=start_row_index + index,
            z_score=start_z_score + (index * 0.55),
            anomaly_direction=anomaly_direction,
            mean=mean,
            standard_deviation=standard_deviation,
            extra_context=extra_context,
        )
        for index in range(count)
    ]


def make_anomaly_finding_with_evidence(
    evidence: list[EvidenceItem],
) -> Finding:
    return Finding(
        title="Anomalies Detected by Anomaly Detection Tool",
        description="Anomalies were detected.",
        severity="HIGH",
        confidence="HIGH",
        evidence=evidence,
        recommended_action=(
            "Investigate the records identified as anomalous for potential operational issues."
        ),
    )


def make_anomaly_finding(
    *,
    metric_name: str = "overtime_hours",
    anomaly_direction: str = "HIGH",
    row_index: int = 42,
) -> Finding:
    return Finding(
        title="Anomalies Detected by Anomaly Detection Tool",
        description="Anomalies were detected.",
        severity="HIGH",
        confidence="HIGH",
        evidence=[
            EvidenceItem(
                description="Anomalous value",
                metric_name=metric_name,
                metric_value=900.0,
                supporting_context={
                    "row_index": row_index,
                    "mean": 100.0,
                    "standard_deviation": 10.0,
                    "z_score": 80.0,
                    "anomaly_direction": anomaly_direction,
                },
            )
        ],
        recommended_action=(
            "Investigate the records identified as anomalous for potential operational issues."
        ),
    )


def make_snapshot_finding(
    *,
    metric_name: str = "attendance_rate",
    period_label: str = "April 2026",
    period_value: float = 88.23,
    baseline_value: float = 86.98,
    delta_vs_baseline: float = 1.25,
    dimension_name: str | None = None,
    highest_entity: str | None = None,
    highest_value: float | None = None,
    lowest_entity: str | None = None,
    lowest_value: float | None = None,
) -> Finding:
    evidence = [
        EvidenceItem(
            description=f"Snapshot value for {period_label}.",
            metric_name=metric_name,
            metric_value=period_value,
            supporting_context={
                "month": "2026-04-01",
                "aggregation": "mean",
                "analysis_mode": "snapshot",
                "period_label": period_label,
                "scoped_row_count": 2,
                "baseline_scope": "full_dataset",
                metric_name: period_value,
            },
        ),
        EvidenceItem(
            description="Full-dataset baseline comparison.",
            metric_name=metric_name,
            metric_value=baseline_value,
            supporting_context={
                "aggregation": "mean",
                "analysis_mode": "snapshot",
                "baseline_scope": "full_dataset",
                "baseline_row_count": 6,
                "baseline_period_count": 4,
                "delta_vs_baseline": delta_vs_baseline,
                metric_name: baseline_value,
            },
        ),
    ]

    if (
        dimension_name
        and highest_entity is not None
        and highest_value is not None
        and lowest_entity is not None
        and lowest_value is not None
    ):
        evidence.extend(
            [
                EvidenceItem(
                    description=f"Highest contributor for {period_label}.",
                    metric_name=metric_name,
                    metric_value=highest_value,
                    supporting_context={
                        "aggregation": "mean",
                        "analysis_mode": "snapshot",
                        "is_snapshot_contributor": True,
                        "contributor_role": "highest",
                        "dimension_name": dimension_name,
                        "entity_name": highest_entity,
                        metric_name: highest_value,
                    },
                ),
                EvidenceItem(
                    description=f"Lowest contributor for {period_label}.",
                    metric_name=metric_name,
                    metric_value=lowest_value,
                    supporting_context={
                        "aggregation": "mean",
                        "analysis_mode": "snapshot",
                        "is_snapshot_contributor": True,
                        "contributor_role": "lowest",
                        "dimension_name": dimension_name,
                        "entity_name": lowest_entity,
                        metric_name: lowest_value,
                    },
                ),
            ]
        )

    return Finding(
        title="Snapshot Summary from Snapshot Analysis Tool",
        description="Snapshot analysis completed.",
        severity="LOW",
        confidence="MEDIUM",
        evidence=evidence,
        recommended_action=(
            "Review the scoped period value against the dataset baseline "
            "to assess operational performance."
        ),
    )
