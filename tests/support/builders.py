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
