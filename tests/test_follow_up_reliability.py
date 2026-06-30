"""Integration tests for capability-aware follow-up suggestion reliability."""

from __future__ import annotations

import pytest

from src.operational_intelligence.investigation_suggestions import (
    MAX_FOLLOW_UP_SUGGESTIONS,
    SUPPORTED_SUGGESTION_TOOLS,
    _BANNED_SUGGESTION_PATTERNS,
    classify_suggestion_capability,
    original_redundant_with_suggestion,
)
from ui.analysis_service import run_analysis
from tests.support.assertions import assert_no_clarification, assert_suggestions_are_humble
from tests.support.factories import (
    education_bundle,
    manufacturing_bundle,
    workforce_bundle,
)


def _assert_reliable_suggestions(suggestions: list[str]) -> None:
    assert suggestions, "Expected at least one follow-up suggestion"
    assert len(suggestions) <= MAX_FOLLOW_UP_SUGGESTIONS
    assert_suggestions_are_humble(suggestions)
    for suggestion in suggestions:
        lowered = suggestion.lower()
        for pattern in _BANNED_SUGGESTION_PATTERNS:
            assert pattern not in lowered, f"Banned pattern {pattern!r} in {suggestion!r}"


def _assert_supported_capabilities(suggestions: list[str]) -> None:
    for suggestion in suggestions:
        capability = classify_suggestion_capability(suggestion)
        assert capability in SUPPORTED_SUGGESTION_TOOLS, suggestion


def _assert_anomaly_suggestions_use_explicit_wording(suggestions: list[str]) -> None:
    anomaly_suggestions = [
        suggestion
        for suggestion in suggestions
        if classify_suggestion_capability(suggestion) == "anomaly_detection"
    ]
    assert anomaly_suggestions, "Expected at least one anomaly follow-up with explicit wording"
    for suggestion in anomaly_suggestions:
        lowered = suggestion.lower()
        assert (
            lowered.startswith("show unusual ")
            or lowered.startswith("list unusual ")
            or lowered.endswith(" are unusual?")
        ), suggestion


def _assert_trend_suggestions_use_supported_wording(suggestions: list[str]) -> None:
    trend_suggestions = [
        suggestion
        for suggestion in suggestions
        if classify_suggestion_capability(suggestion) == "trend_analysis"
    ]
    for suggestion in trend_suggestions:
        lowered = suggestion.lower()
        assert lowered.startswith("how has ") and lowered.endswith(" changed over time?"), suggestion


def _assert_variance_suggestions_use_supported_wording(suggestions: list[str]) -> None:
    variance_suggestions = [
        suggestion
        for suggestion in suggestions
        if classify_suggestion_capability(suggestion) == "variance_analysis"
    ]
    for suggestion in variance_suggestions:
        lowered = suggestion.lower()
        assert (
            (" has the highest " in lowered and lowered.startswith("which "))
            or (" has the lowest " in lowered and lowered.startswith("which "))
            or (lowered.startswith("compare ") and " across " in lowered)
        ), suggestion


def _assert_uses_dataset_vocabulary(
    suggestions: list[str],
    *,
    allowed_dimensions: set[str],
    allowed_metrics: set[str],
) -> None:
    dimension_labels = {dimension.replace("_", " ") for dimension in allowed_dimensions}
    metric_labels = {metric.replace("_", " ") for metric in allowed_metrics}
    for suggestion in suggestions:
        lowered = suggestion.lower()
        capability = classify_suggestion_capability(suggestion)
        if capability == "variance_analysis":
            assert any(label in lowered for label in dimension_labels), suggestion
            assert any(label in lowered for label in metric_labels), suggestion
        if capability == "anomaly_detection":
            assert any(label in lowered for label in metric_labels), suggestion
        if capability == "trend_analysis":
            assert any(label in lowered for label in metric_labels), suggestion


def _assert_no_original_question_duplicates(
    suggestions: list[str],
    original_question: str,
) -> None:
    for suggestion in suggestions:
        assert not original_redundant_with_suggestion(
            original_question,
            suggestion,
        ), suggestion


@pytest.mark.integration
class TestFollowUpReliabilityGoldenDatasets:
    @pytest.mark.parametrize(
        ("bundle_fn", "question", "allowed_dimensions", "allowed_metrics"),
        [
            (
                manufacturing_bundle,
                "How has downtime_minutes changed over time?",
                {"production_line", "shift", "site", "supervisor"},
                {"downtime_minutes", "defects", "units_produced"},
            ),
            (
                education_bundle,
                "Which school has the lowest attendance?",
                {"school", "year_level", "campus", "program_type"},
                {"attendance_rate", "behaviour_incidents", "average_score"},
            ),
            (
                workforce_bundle,
                "What looks unusual?",
                {"department", "employee_name", "location", "manager", "employment_type"},
                {"hours", "overtime_hours", "absence_days"},
            ),
        ],
    )
    def test_pipeline_suggestions_are_dataset_and_tool_aware(
        self,
        bundle_fn,
        question,
        allowed_dimensions,
        allowed_metrics,
    ):
        df, profile = bundle_fn()
        result = run_analysis(question, df, profile)

        assert_no_clarification(result)
        assert result.report is not None
        suggestions = result.report.suggested_follow_up_investigations

        _assert_reliable_suggestions(suggestions)
        _assert_supported_capabilities(suggestions)
        _assert_no_original_question_duplicates(suggestions, question)
        _assert_uses_dataset_vocabulary(
            suggestions,
            allowed_dimensions=allowed_dimensions,
            allowed_metrics=allowed_metrics,
        )
        if question.lower().startswith("what looks unusual"):
            assert not any(
                classify_suggestion_capability(suggestion) == "anomaly_detection"
                for suggestion in suggestions
            )
        if "changed over time" in question.lower():
            _assert_trend_suggestions_use_supported_wording(suggestions)
        if "lowest" in question.lower() or "highest" in question.lower():
            _assert_variance_suggestions_use_supported_wording(suggestions)

    @pytest.mark.parametrize(
        ("bundle_fn", "question"),
        [
            (manufacturing_bundle, "How has downtime_minutes changed over time?"),
            (education_bundle, "Which school has the lowest attendance?"),
            (workforce_bundle, "What looks unusual?"),
        ],
    )
    def test_suggestions_do_not_repeat_generic_templates(self, bundle_fn, question):
        df, profile = bundle_fn()
        result = run_analysis(question, df, profile)

        assert result.report is not None
        _assert_reliable_suggestions(result.report.suggested_follow_up_investigations)

    @pytest.mark.parametrize(
        ("bundle_fn", "question"),
        [
            (manufacturing_bundle, "How has downtime_minutes changed over time?"),
            (education_bundle, "Which school has the lowest attendance?"),
            (workforce_bundle, "What looks unusual?"),
        ],
    )
    def test_suggestions_execute_with_deterministic_findings(self, bundle_fn, question):
        df, profile = bundle_fn()
        result = run_analysis(question, df, profile)

        assert result.report is not None
        suggestions = result.report.suggested_follow_up_investigations
        _assert_supported_capabilities(suggestions)

        for suggestion in suggestions:
            follow_up = run_analysis(suggestion, df, profile)
            assert_no_clarification(follow_up)
            assert follow_up.findings, (
                f"Follow-up produced no findings (capability mismatch): {suggestion!r}"
            )

    @pytest.mark.parametrize(
        ("bundle_fn", "question"),
        [
            (
                manufacturing_bundle,
                "Which production line has the highest defects?",
            ),
            (
                education_bundle,
                "How has attendance changed over time?",
            ),
            (
                workforce_bundle,
                "What looks unusual and what should I investigate?",
            ),
        ],
    )
    def test_suggestions_extend_without_repeating_original_question(
        self,
        bundle_fn,
        question,
    ):
        df, profile = bundle_fn()
        result = run_analysis(question, df, profile)

        assert_no_clarification(result)
        assert result.report is not None
        suggestions = result.report.suggested_follow_up_investigations

        _assert_reliable_suggestions(suggestions)
        _assert_supported_capabilities(suggestions)
        _assert_no_original_question_duplicates(suggestions, question)
