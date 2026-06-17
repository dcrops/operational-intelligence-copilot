"""Unit tests for snapshot bucket detection and SnapshotAnalysisTool."""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.snapshot_analysis import (
    BASELINE_SCOPE,
    SnapshotAnalysisTool,
    build_snapshot_context,
    count_distinct_temporal_buckets,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def monthly_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": [
                "2026-01-01",
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
                "2026-04-01",
            ],
            "school": ["A", "B", "A", "A", "A", "B"],
            "attendance_rate": [90.0, 88.0, 91.0, 92.0, 95.0, 72.0],
        }
    )


class TestCountDistinctTemporalBuckets:
    def test_single_bucket(self, monthly_df: pd.DataFrame):
        april = monthly_df[monthly_df["month"] == "2026-04-01"]

        assert count_distinct_temporal_buckets(april, "month") == 1

    def test_three_buckets(self, monthly_df: pd.DataFrame):
        q1 = monthly_df[monthly_df["month"].isin(
            ["2026-01-01", "2026-02-01", "2026-03-01"]
        )]

        assert count_distinct_temporal_buckets(q1, "month") == 3

    def test_duplicate_rows_in_same_bucket_count_once(self, monthly_df: pd.DataFrame):
        april = monthly_df[monthly_df["month"] == "2026-04-01"]

        assert len(april) == 2
        assert count_distinct_temporal_buckets(april, "month") == 1

    def test_twelve_buckets_for_full_year(self):
        df = pd.DataFrame(
            {
                "month": pd.date_range("2026-01-01", periods=12, freq="MS"),
                "value": list(range(12)),
            }
        )

        assert count_distinct_temporal_buckets(df, "month") == 12


class TestBuildSnapshotContext:
    def test_returns_context_for_single_bucket(self, monthly_df: pd.DataFrame):
        april = monthly_df[monthly_df["month"] == "2026-04-01"]
        context = build_snapshot_context(
            april,
            "month",
            temporal_period_label="April 2026",
        )

        assert context is not None
        assert context.activated is True
        assert context.period_label == "April 2026"
        assert context.bucket_count == 1

    def test_returns_none_for_multiple_buckets(self, monthly_df: pd.DataFrame):
        assert build_snapshot_context(monthly_df, "month") is None


class TestSnapshotAnalysisTool:
    def test_baseline_delta_and_record_counts(self, monthly_df: pd.DataFrame):
        scoped = monthly_df[monthly_df["month"] == "2026-04-01"]
        tool = SnapshotAnalysisTool()

        result = tool.analyze(
            scoped,
            monthly_df,
            "month",
            "attendance_rate",
            aggregation="mean",
            period_label="April 2026",
        )

        assert result.success is True
        assert result.tool_name == "snapshot_analysis"
        assert "April 2026" in result.summary

        baseline_item = next(
            item
            for item in result.evidence_items
            if item.description == "Full-dataset baseline comparison."
        )
        snapshot_item = next(
            item
            for item in result.evidence_items
            if item.description == "Snapshot value for April 2026."
        )

        period_value = float(snapshot_item.metric_value)
        baseline_value = float(baseline_item.metric_value)
        delta = float(baseline_item.supporting_context["delta_vs_baseline"])

        assert period_value == pytest.approx(83.5)
        assert baseline_value == pytest.approx(88.875)
        assert delta == pytest.approx(period_value - baseline_value)
        assert snapshot_item.supporting_context["baseline_scope"] == BASELINE_SCOPE
        assert snapshot_item.supporting_context["scoped_row_count"] == 2
        assert baseline_item.supporting_context["baseline_row_count"] == 6
        assert baseline_item.supporting_context["baseline_period_count"] == 4

    def test_sum_aggregation_uses_average_monthly_baseline(self, monthly_df: pd.DataFrame):
        df = monthly_df.assign(units=[10, 20, 30, 40, 50, 60])
        scoped = df[df["month"] == "2026-04-01"]

        result = SnapshotAnalysisTool().analyze(
            scoped,
            df,
            "month",
            "units",
            aggregation="sum",
            period_label="April 2026",
        )

        snapshot_item = result.evidence_items[0]
        baseline_item = result.evidence_items[1]

        assert float(snapshot_item.metric_value) == 110.0
        assert float(baseline_item.metric_value) == pytest.approx(52.5)
        assert float(baseline_item.supporting_context["delta_vs_baseline"]) == pytest.approx(57.5)
