from src.operational_intelligence.question_semantics import DEFAULT_AGGREGATION, infer_aggregation_type
from src.operational_intelligence.trend_analysis import TrendAnalysisTool
from src.operational_intelligence.variance_analysis import VarianceAnalysisTool
from tests.support.factories import (
    EDUCATION_LOWEST_ATTENDANCE_SCHOOL,
    make_education_df,
    make_manufacturing_df,
)


def test_trend_uses_mean_for_rate_metrics():
    df = make_education_df()

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
    df = make_education_df()

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
    assert target.supporting_context["school"] == EDUCATION_LOWEST_ATTENDANCE_SCHOOL
    assert target.supporting_context["comparison_direction"] == "bottom"
    assert "lowest mean" in result.summary


def test_variance_dual_direction_marks_both_targets():
    df = make_manufacturing_df()[["production_line", "defects"]].drop_duplicates()

    result = VarianceAnalysisTool().analyze(
        df,
        "production_line",
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
