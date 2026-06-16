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
