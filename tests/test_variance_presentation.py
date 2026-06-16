import pytest

from tests.support.builders import (
    make_variance_evidence_item,
    make_variance_finding,
)
from ui.variance_presentation import variance_business_description


@pytest.mark.unit
def test_top_comparison_uses_highest_wording():
    finding = make_variance_finding(
        [
            make_variance_evidence_item(
                dimension_key="production_line",
                dimension_value="Line B",
                metric_name="defects",
                metric_value=32.0,
                aggregation="sum",
                comparison_direction="top",
            )
        ]
    )

    description = variance_business_description(finding, "defects")

    assert "highest total defects" in description
    assert "Line B" in description
    assert "lowest" not in description


@pytest.mark.unit
def test_bottom_comparison_uses_lowest_wording():
    finding = make_variance_finding(
        [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School B",
                    metric_name="attendance_rate",
                    metric_value=71.0,
                    aggregation="mean",
                    comparison_direction="bottom",
                )
        ]
    )

    description = variance_business_description(finding, "attendance rate")

    assert "lowest mean attendance rate" in description
    assert "School B" in description
    assert "highest" not in description


@pytest.mark.unit
def test_dual_comparison_mentions_highest_and_lowest_groups():
    finding = make_variance_finding(
        [
            make_variance_evidence_item(
                dimension_key="department",
                dimension_value="Ops",
                metric_name="hours",
                metric_value=600.0,
                aggregation="sum",
                comparison_direction="dual",
                comparison_extreme="top",
            ),
            make_variance_evidence_item(
                dimension_key="department",
                dimension_value="HR",
                metric_name="hours",
                metric_value=480.0,
                aggregation="sum",
                comparison_direction="dual",
                comparison_extreme="bottom",
            ),
        ]
    )

    description = variance_business_description(finding, "hours")

    assert "highest total hours" in description
    assert "lowest total hours" in description
    assert "Ops" in description
    assert "HR" in description


@pytest.mark.unit
def test_presentation_reads_direction_and_aggregation_from_evidence_metadata():
    finding = make_variance_finding(
        [
            make_variance_evidence_item(
                dimension_key="department",
                dimension_value="HR",
                metric_name="hours",
                metric_value=480.0,
                aggregation="sum",
                comparison_direction="bottom",
            )
        ]
    )
    target = next(
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target")
    )

    description = variance_business_description(finding, "hours")

    assert target.supporting_context["comparison_direction"] == "bottom"
    assert target.supporting_context["aggregation"] == "sum"
    assert "lowest total hours" in description
