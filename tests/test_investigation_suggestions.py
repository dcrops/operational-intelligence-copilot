"""Unit tests for deterministic investigation suggestion generation."""

from __future__ import annotations

import pytest

from src.operational_intelligence.investigation_suggestions import InvestigationSuggestionGenerator
from tests.support.assertions import assert_suggestions_are_humble
from tests.support.builders import (
    make_anomaly_finding,
    make_trend_finding,
    make_variance_evidence_item,
    make_variance_finding,
)


@pytest.fixture
def generator() -> InvestigationSuggestionGenerator:
    return InvestigationSuggestionGenerator()


@pytest.mark.unit
class TestTrendSuggestions:
    def test_generates_three_base_suggestions(self, generator):
        finding = make_trend_finding(metric_name="attendance_rate")
        suggestions = generator.generate_for_finding(finding)

        assert len(suggestions) == 3
        assert suggestions[0].startswith(
            "Investigate whether attendance rate changes are concentrated in specific periods."
        )
        assert "particular groups contributed disproportionately" in suggestions[1]
        assert "related metrics also changed" in suggestions[2]

    def test_volatile_trend_adds_fourth_suggestion(self, generator):
        finding = make_trend_finding(metric_name="downtime minutes", trend_label="volatile")
        suggestions = generator.generate_for_finding(finding)

        assert len(suggestions) == 4
        assert "short-term volatility" in suggestions[-1]
        assert "may warrant" in suggestions[-1]

    def test_group_metadata_uses_group_contribution_wording(self, generator):
        finding = make_trend_finding(
            metric_name="hours",
            with_group_metadata=True,
            dimension_key="department",
        )
        suggestions = generator.generate_for_finding(finding)

        assert "Review which groups contributed most to the change in hours." in suggestions


@pytest.mark.unit
class TestVarianceSuggestions:
    def test_generates_three_base_suggestions(self, generator):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School A",
                    metric_name="attendance_rate",
                    metric_value=88.0,
                    aggregation="mean",
                    comparison_direction="top",
                )
            ]
        )
        suggestions = generator.generate_for_finding(finding)

        assert len(suggestions) == 3
        assert "school values contributed most" in suggestions[0]
        assert "changed over time" in suggestions[1]
        assert "related metrics are also elevated" in suggestions[2]

    def test_dual_variance_adds_gap_suggestion(self, generator):
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
        suggestions = generator.generate_for_finding(finding)

        assert len(suggestions) == 4
        assert "gap between the highest and lowest groups" in suggestions[-1]

    def test_missing_dimension_uses_fallback_wording(self, generator):
        finding = make_variance_finding([])
        suggestions = generator.generate_for_finding(finding)

        assert suggestions[0].startswith(
            "Review whether particular groups contributed disproportionately"
        )


@pytest.mark.unit
class TestAnomalySuggestions:
    def test_generates_three_suggestions(self, generator):
        finding = make_anomaly_finding(metric_name="overtime_hours")
        suggestions = generator.generate_for_finding(finding)

        assert len(suggestions) == 3
        assert "clustered by group" in suggestions[0]
        assert "concentrated in specific time periods" in suggestions[1]
        assert "same records appear unusual across multiple metrics" in suggestions[2]


@pytest.mark.unit
class TestSuggestionAggregation:
    def test_orders_by_type_anomaly_variance_trend(self, generator):
        trend = make_trend_finding(metric_name="hours")
        variance = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="department",
                    dimension_value="Ops",
                    metric_name="hours",
                    metric_value=600.0,
                    aggregation="sum",
                    comparison_direction="top",
                )
            ]
        )
        anomaly = make_anomaly_finding(metric_name="overtime_hours")

        suggestions = generator.generate_for_findings([trend, variance, anomaly])

        assert suggestions.index(
            "Investigate whether anomalies in overtime hours are clustered by group."
        ) < suggestions.index("Examine whether this difference has changed over time.")
        assert suggestions.index("Examine whether this difference has changed over time.") < suggestions.index(
            "Investigate whether hours changes are concentrated in specific periods."
        )

    def test_deduplicates_while_preserving_first_order(self, generator):
        trend_a = make_trend_finding(metric_name="hours")
        variance = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="department",
                    dimension_value="Ops",
                    metric_name="hours",
                    metric_value=600.0,
                    aggregation="sum",
                    comparison_direction="top",
                )
            ]
        )
        trend_b = make_trend_finding(metric_name="hours")

        suggestions = generator.generate_for_findings([trend_a, variance, trend_b])
        duplicate = "Investigate whether hours changes are concentrated in specific periods."
        assert suggestions.count(duplicate) == 1

    def test_empty_findings_returns_empty_list(self, generator):
        assert generator.generate_for_findings([]) == []

    def test_unknown_finding_type_generates_no_suggestions(self, generator):
        from src.operational_intelligence.models import Finding

        finding = Finding(
            title="Informational Finding",
            description="Context only.",
            severity="INFO",
            confidence="LOW",
            evidence=[],
        )
        assert generator.generate_for_finding(finding) == []


@pytest.mark.unit
class TestSuggestionSafety:
    def test_sample_findings_suggestions_are_humble_and_non_causal(self, generator):
        from tests.support.builders import make_sample_findings

        suggestions = generator.generate_for_findings(make_sample_findings())
        assert_suggestions_are_humble(suggestions)
