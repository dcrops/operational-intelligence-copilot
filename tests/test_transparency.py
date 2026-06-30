import pytest

from src.operational_intelligence.models import AnalysisRequest, EvidenceItem, Finding, SnapshotContext, TemporalFilterContext
from ui.transparency import (
    format_auto_resolved_trail,
    format_clarification_trail,
    format_metrics_analysed_trail,
    format_snapshot_contributors_trail,
    format_snapshot_trail,
    format_temporal_filter_trail,
    resolve_metrics_analysed,
)
from tests.support.builders import make_anomaly_finding, make_variance_evidence_item, make_variance_finding
from tests.support.factories import manufacturing_bundle

pytestmark = pytest.mark.unit


def _request(question: str = "Sample question", **kwargs) -> AnalysisRequest:
    return AnalysisRequest(question=question, dataset_names=["sample"], **kwargs)


def test_format_temporal_filter_trail_includes_inferred_date_column():
    temporal_filter = TemporalFilterContext(
        label="Q1 2026",
        date_column="month",
        original_row_count=180,
        filtered_row_count=90,
        date_column_inferred=True,
    )

    lines = format_temporal_filter_trail(temporal_filter)

    assert lines == [
        "Period: Q1 2026",
        "Date column: month",
        "Records analysed: 90 of 180",
        "Date column inferred: month",
    ]


def test_format_temporal_filter_trail_omits_inferred_line_when_explicit():
    temporal_filter = TemporalFilterContext(
        label="April 2026",
        date_column="month",
        original_row_count=12,
        filtered_row_count=3,
        date_column_inferred=False,
    )

    assert format_temporal_filter_trail(temporal_filter) == [
        "Period: April 2026",
        "Date column: month",
        "Records analysed: 3 of 12",
    ]


def test_format_snapshot_trail_includes_period_reason_and_analysis_mode():
    snapshot_context = SnapshotContext(
        activated=True,
        reason="Only one temporal period remained in the scoped dataset.",
        period_label="April 2026",
        bucket_count=1,
    )

    assert format_snapshot_trail(snapshot_context) == [
        "Period: April 2026",
        "Reason: Only one temporal period remained in the scoped dataset.",
        "Analysis: Snapshot Intelligence",
    ]


def test_format_clarification_trail_metric_only():
    lines = format_clarification_trail(
        _request(selected_metrics=["hours"])
    )

    assert lines == ["Metric selected: Hours"]


def test_format_clarification_trail_multi_step_selections():
    lines = format_clarification_trail(
        _request(
            selected_metrics=["units_produced"],
            selected_dimensions=["production_line"],
            requested_analysis_type="variance_analysis",
            selected_comparison_direction="bottom",
        )
    )

    assert lines == [
        "Metric selected: Units Produced",
        "Dimension selected: production_line",
        "Analysis type selected: variance_analysis",
        "Comparison direction selected: bottom",
    ]


def test_format_clarification_trail_empty_request():
    assert format_clarification_trail(_request()) == []


def test_format_auto_resolved_trail_single_metric_inferred_and_aggregation_inferred():
    finding = Finding(
        title="Trend Identified by Trend Analysis Tool",
        description="Trend summary.",
        severity="LOW",
        confidence="MEDIUM",
        evidence=[
            EvidenceItem(
                description="Period value",
                metric_name="attendance_rate",
                metric_value=89.82,
                supporting_context={
                    "month": "2026-01-01",
                    "attendance_rate": 89.82,
                    "aggregation": "mean",
                },
            )
        ],
    )

    lines = format_auto_resolved_trail(
        _request(),
        [finding],
        ["trend_analysis"],
    )

    assert lines == [
        "Metric inferred: Attendance Rate",
        "Aggregation inferred: mean",
    ]


def test_format_auto_resolved_trail_variance_dimension_and_comparison_inferred():
    finding = make_variance_finding(
        [
            make_variance_evidence_item(
                dimension_key="school",
                dimension_value="School C",
                metric_name="attendance_rate",
                metric_value=83.66,
                aggregation="mean",
                comparison_direction="bottom",
            )
        ]
    )

    lines = format_auto_resolved_trail(
        _request(),
        [finding],
        ["variance_analysis"],
    )

    assert "Metric inferred: Attendance Rate" in lines
    assert "Dimension inferred: school" in lines
    assert "Aggregation inferred: mean" in lines
    assert "Comparison direction inferred: bottom" in lines


def test_format_auto_resolved_trail_excludes_user_selected_fields():
    finding = make_variance_finding(
        [
            make_variance_evidence_item(
                dimension_key="school",
                dimension_value="School C",
                metric_name="attendance_rate",
                metric_value=83.66,
                aggregation="mean",
                comparison_direction="bottom",
            )
        ]
    )

    lines = format_auto_resolved_trail(
        _request(
            selected_metrics=["attendance_rate"],
            selected_dimensions=["school"],
            selected_comparison_direction="bottom",
        ),
        [finding],
        ["variance_analysis"],
    )

    assert lines == ["Aggregation inferred: mean"]


def test_format_auto_resolved_trail_empty_when_no_findings():
    assert format_auto_resolved_trail(_request(), [], ["trend_analysis"]) == []


def test_format_metrics_analysed_trail_lists_multi_metric_anomaly_metrics():
    metrics = format_metrics_analysed_trail(
        ["defects", "downtime_minutes", "units_produced"]
    )

    assert metrics == ["Defects", "Downtime Minutes", "Units Produced"]


def test_multi_metric_anomaly_does_not_show_metrics_under_auto_resolved():
    findings = [make_anomaly_finding(metric_name="units_produced")]
    metrics_analysed = ["defects", "downtime_minutes", "units_produced"]

    auto_resolved = format_auto_resolved_trail(
        _request(),
        findings,
        ["anomaly_detection"],
        metrics_analysed=metrics_analysed,
    )

    assert auto_resolved == []
    assert not any("Metric" in line for line in auto_resolved)


def test_single_metric_anomaly_still_shows_metric_inferred():
    finding = make_anomaly_finding(metric_name="overtime_hours")

    auto_resolved = format_auto_resolved_trail(
        _request(),
        [finding],
        ["anomaly_detection"],
        metrics_analysed=["overtime_hours"],
    )
    metrics_analysed = format_metrics_analysed_trail(["overtime_hours"])

    assert auto_resolved == ["Metric inferred: Overtime Hours"]
    assert metrics_analysed == []


def test_resolve_metrics_analysed_for_unscoped_anomaly_question():
    _, profile = manufacturing_bundle()

    metrics = resolve_metrics_analysed(
        _request(question="What looks unusual?"),
        ["anomaly_detection"],
        profile.potential_metrics,
    )

    assert len(metrics) > 1
