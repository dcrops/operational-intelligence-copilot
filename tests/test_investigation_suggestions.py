"""Unit tests for capability-aware investigation suggestion generation."""

from __future__ import annotations

import pytest

from src.operational_intelligence.investigation_suggestions import (
    MAX_FOLLOW_UP_SUGGESTIONS,
    SUPPORTED_SUGGESTION_TOOLS,
    _BANNED_SUGGESTION_PATTERNS,
    InvestigationSuggestionGenerator,
    classify_suggestion_capability,
    filter_duplicate_priority_actions,
    is_equivalent_question,
    original_redundant_with_suggestion,
)
from src.operational_intelligence.models import DatasetProfile, Finding
from tests.support.assertions import assert_suggestions_are_humble
from tests.support.builders import (
    make_anomaly_finding,
    make_suggestion_profile,
    make_trend_finding,
    make_variance_evidence_item,
    make_variance_finding,
)


@pytest.fixture
def profile() -> DatasetProfile:
    return make_suggestion_profile()


@pytest.fixture
def generator(profile: DatasetProfile) -> InvestigationSuggestionGenerator:
    return InvestigationSuggestionGenerator()


def _assert_no_banned_patterns(suggestions: list[str]) -> None:
    for suggestion in suggestions:
        lowered = suggestion.lower()
        for pattern in _BANNED_SUGGESTION_PATTERNS:
            assert pattern not in lowered, f"Banned pattern {pattern!r} in {suggestion!r}"


def _assert_supported_capabilities(suggestions: list[str]) -> None:
    for suggestion in suggestions:
        capability = classify_suggestion_capability(suggestion)
        assert capability in SUPPORTED_SUGGESTION_TOOLS, suggestion


@pytest.mark.unit
class TestTrendSuggestions:
    def test_generates_supported_trend_question(self, profile):
        finding = make_trend_finding(metric_name="attendance_rate")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "How has attendance rate changed over time?"
        assert len(suggestions) <= MAX_FOLLOW_UP_SUGGESTIONS
        _assert_no_banned_patterns(suggestions)

    def test_volatile_trend_does_not_add_unsupported_follow_up(self, profile):
        finding = make_trend_finding(metric_name="downtime minutes", trend_label="volatile")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "How has downtime minutes changed over time?"
        assert not any("volatility" in suggestion for suggestion in suggestions)
        _assert_no_banned_patterns(suggestions)

    def test_trend_without_date_columns_omits_trend_suggestion(self):
        profile = make_suggestion_profile(date_columns=[], column_names=["department", "hours"])
        finding = make_trend_finding(metric_name="hours")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert not any(
            classify_suggestion_capability(suggestion) == "trend_analysis"
            for suggestion in suggestions
        )

    def test_trend_without_trend_tool_returns_no_trend_suggestion(self, profile):
        limited_profile = make_suggestion_profile(
            suitable_tools=["variance_analysis", "anomaly_detection"],
        )
        finding = make_trend_finding(metric_name="hours")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=limited_profile,
        )

        assert not any(
            classify_suggestion_capability(suggestion) == "trend_analysis"
            for suggestion in suggestions
        )


@pytest.mark.unit
class TestVarianceSuggestions:
    def test_top_variance_uses_highest_comparison_wording(self, profile):
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
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "Which school has the highest attendance rate?"
        assert any("has the lowest attendance rate" in suggestion for suggestion in suggestions)
        _assert_no_banned_patterns(suggestions)

    def test_bottom_variance_uses_lowest_comparison_wording(self, profile):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School B",
                    metric_name="attendance_rate",
                    metric_value=70.0,
                    aggregation="mean",
                    comparison_direction="bottom",
                )
            ]
        )
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "Which school has the lowest attendance rate?"
        assert any("has the highest attendance rate" in suggestion for suggestion in suggestions)
        _assert_no_banned_patterns(suggestions)

    def test_dual_variance_uses_compare_across_wording(self, profile):
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
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "Compare hours across department."
        _assert_no_banned_patterns(suggestions)

    def test_missing_dimension_returns_no_variance_suggestion(self, profile):
        profile = make_suggestion_profile(potential_dimensions=[])
        finding = make_variance_finding([])
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions == []


@pytest.mark.unit
class TestAnomalySuggestions:
    def test_generates_explicit_anomaly_suggestion(self, profile):
        finding = make_anomaly_finding(metric_name="overtime_hours")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
        )

        assert suggestions[0] == "Show unusual overtime hours records."
        assert any("unusual" in suggestion.lower() for suggestion in suggestions)
        _assert_no_banned_patterns(suggestions)

    def test_anomaly_without_tool_returns_no_anomaly_suggestion(self, profile):
        limited_profile = make_suggestion_profile(suitable_tools=["trend_analysis"])
        finding = make_anomaly_finding(metric_name="overtime_hours")
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=limited_profile,
        )

        assert not any(
            classify_suggestion_capability(suggestion) == "anomaly_detection"
            for suggestion in suggestions
        )


@pytest.mark.unit
class TestSuggestionAggregation:
    def test_orders_by_type_anomaly_variance_trend(self, profile):
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

        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [trend, variance, anomaly],
            profile=profile,
        )

        assert suggestions[0] == "Show unusual overtime hours records."
        assert len(suggestions) <= MAX_FOLLOW_UP_SUGGESTIONS
        _assert_supported_capabilities(suggestions)

    def test_deduplicates_while_preserving_first_order(self, profile):
        trend_a = make_trend_finding(metric_name="hours")
        trend_b = make_trend_finding(metric_name="hours")

        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [trend_a, trend_b],
            profile=profile,
        )
        duplicate = "How has hours changed over time?"
        assert suggestions.count(duplicate) == 1

    def test_empty_findings_returns_empty_list(self, generator):
        assert generator.generate_for_findings([]) == []

    def test_unknown_finding_type_generates_no_suggestions(self, generator):
        finding = Finding(
            title="Informational Finding",
            description="Context only.",
            severity="INFO",
            confidence="LOW",
            evidence=[],
        )
        assert generator.generate_for_finding(finding) == []


@pytest.mark.unit
class TestPriorityActionDedup:
    def test_filter_duplicate_priority_actions_removes_substantial_overlap(self):
        suggestions = [
            "Show unusual hours records.",
            "How has hours changed over time?",
        ]
        priority_actions = [
            "Show unusual hours records.",
        ]

        filtered = filter_duplicate_priority_actions(suggestions, priority_actions)

        assert filtered == ["How has hours changed over time?"]


@pytest.mark.unit
class TestOriginalQuestionDedup:
    def test_equivalent_questions_ignore_case_and_punctuation(self):
        original = "Which production line has the highest defects?"
        duplicate = "Which production line has the highest Defects?"
        assert is_equivalent_question(duplicate, original)

    def test_highest_variance_question_is_not_repeated(self, profile):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="production_line",
                    dimension_value="Line B",
                    metric_name="defects",
                    metric_value=8.0,
                    aggregation="sum",
                    comparison_direction="top",
                )
            ]
        )
        original = "Which production line has the highest defects?"
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
            original_question=original,
        )

        assert suggestions
        assert not any(
            original_redundant_with_suggestion(original, suggestion) for suggestion in suggestions
        )
        assert not any("has the highest defects" in suggestion.lower() for suggestion in suggestions)
        assert any("has the lowest defects" in suggestion.lower() for suggestion in suggestions)

    def test_trend_question_is_not_repeated(self, profile):
        finding = make_trend_finding(metric_name="attendance_rate")
        original = "How has attendance changed over time?"
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
            original_question=original,
        )

        assert suggestions
        assert not any(
            classify_suggestion_capability(suggestion) == "trend_analysis"
            for suggestion in suggestions
        )

    def test_anomaly_question_is_not_repeated(self, profile):
        finding = make_anomaly_finding(metric_name="attendance_rate")
        original = "What looks unusual and what should I investigate?"
        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            [finding],
            profile=profile,
            original_question=original,
        )

        assert suggestions
        assert not any(
            classify_suggestion_capability(suggestion) == "anomaly_detection"
            for suggestion in suggestions
        )
        _assert_supported_capabilities(suggestions)


@pytest.mark.unit
class TestSuggestionSafety:
    def test_sample_findings_suggestions_are_supported_and_non_causal(self, profile):
        from tests.support.builders import make_sample_findings

        suggestions = InvestigationSuggestionGenerator().generate_for_findings(
            make_sample_findings(),
            profile=profile,
        )
        assert_suggestions_are_humble(suggestions)
        _assert_no_banned_patterns(suggestions)
        _assert_supported_capabilities(suggestions)
        assert len(suggestions) <= MAX_FOLLOW_UP_SUGGESTIONS
