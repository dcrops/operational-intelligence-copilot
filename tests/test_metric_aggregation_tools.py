import pandas as pd

from src.operational_intelligence.question_semantics import DEFAULT_AGGREGATION, infer_aggregation_type
from src.operational_intelligence.trend_analysis import TrendAnalysisTool
from src.operational_intelligence.variance_analysis import VarianceAnalysisTool


def test_trend_uses_mean_for_rate_metrics():
    dates = pd.date_range("2026-01-01", periods=3, freq="MS")
    df = pd.DataFrame(
        {
            "month": dates,
            "school": ["A", "A", "A"],
            "attendance_rate": [80.0, 90.0, 70.0],
        }
    )

    result = TrendAnalysisTool().analyze(
        df,
        "month",
        "attendance_rate",
        aggregation=infer_aggregation_type("attendance_rate"),
    )

    assert result.success is True
    assert result.evidence_items[0].supporting_context["aggregation"] == "mean"
    assert result.evidence_items[0].metric_value == 80.0


def test_variance_uses_bottom_direction_and_mean():
    df = pd.DataFrame(
        {
            "school": ["North", "North", "South", "South"],
            "attendance_rate": [95.0, 94.0, 70.0, 72.0],
        }
    )

    result = VarianceAnalysisTool().analyze(
        df,
        "school",
        "attendance_rate",
        aggregation=infer_aggregation_type("attendance_rate"),
        comparison_direction="bottom",
    )

    assert result.success is True
    target = next(
        item
        for item in result.evidence_items
        if item.supporting_context.get("is_comparison_target")
    )
    assert target.supporting_context["school"] == "South"
    assert target.supporting_context["comparison_direction"] == "bottom"
    assert "lowest mean" in result.summary


def test_variance_dual_direction_marks_both_targets():
    df = pd.DataFrame(
        {
            "school": ["North", "South", "East"],
            "defects": [10, 2, 5],
        }
    )

    result = VarianceAnalysisTool().analyze(
        df,
        "school",
        "defects",
        aggregation=infer_aggregation_type("defects"),
        comparison_direction="dual",
    )

    targets = [
        item
        for item in result.evidence_items
        if item.supporting_context.get("is_comparison_target")
    ]
    assert len(targets) == 2
    assert infer_aggregation_type("defects") == DEFAULT_AGGREGATION
