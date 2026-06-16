"""Behavioural assertion helpers for pipeline and analysis tests."""

from __future__ import annotations

import pytest

from src.operational_intelligence.models import ClarificationRequest, Finding
from ui.models import AnalysisResult


def _unwrap_clarification(result) -> ClarificationRequest | None:
    if isinstance(result, ClarificationRequest):
        return result
    if isinstance(result, AnalysisResult):
        return result.clarification
    return None


def assert_clarification(
    result,
    clarification_type: str,
    options: list[str] | None = None,
) -> ClarificationRequest:
    clarification = _unwrap_clarification(result)
    assert clarification is not None, "Expected a clarification request"
    assert clarification.clarification_type == clarification_type
    if options is not None:
        assert clarification.options == options
    return clarification


def assert_no_clarification(result) -> None:
    if isinstance(result, ClarificationRequest):
        pytest.fail("Expected analysis findings, got ClarificationRequest")
    if isinstance(result, AnalysisResult):
        assert result.clarification is None
        return
    assert isinstance(result, list), "Expected findings list or AnalysisResult"


def _variance_finding(findings: list[Finding]) -> Finding:
    return next(f for f in findings if "variance" in f.title.lower())


def _trend_finding(findings: list[Finding]) -> Finding:
    return next(f for f in findings if "trend" in f.title.lower())


def _variance_targets(finding: Finding):
    return [
        item
        for item in finding.evidence
        if item.supporting_context.get("is_comparison_target") is True
    ]


def assert_variance_outcome(
    findings: list[Finding],
    *,
    expected_metric: str,
    expected_dimension: str,
    expected_aggregation: str,
    expected_direction: str,
    expected_targets: list[str] | None = None,
) -> None:
    finding = _variance_finding(findings)
    targets = _variance_targets(finding)
    assert targets, "Expected comparison target evidence rows"

    if expected_direction == "dual":
        assert len(targets) >= 2
        target_values = [
            item.supporting_context.get(expected_dimension) for item in targets
        ]
        if expected_targets is not None:
            assert set(target_values) == set(expected_targets)
    else:
        assert len(targets) == 1
        target = targets[0]
        assert target.metric_name == expected_metric
        assert target.supporting_context.get("comparison_direction") == expected_direction
        assert target.supporting_context.get("aggregation") == expected_aggregation
        dimension_value = target.supporting_context.get(expected_dimension)
        assert dimension_value is not None
        if expected_targets is not None:
            assert dimension_value == expected_targets[0]

    for target in targets:
        assert target.metric_name == expected_metric
        assert target.supporting_context.get("aggregation") == expected_aggregation


def assert_trend_outcome(
    findings: list[Finding],
    *,
    expected_metric: str,
    expected_aggregation: str,
) -> None:
    finding = _trend_finding(findings)
    period_items = [
        item
        for item in finding.evidence
        if item.metric_value is not None
        and "Trend classification" not in item.description
    ]
    assert period_items, "Expected trend period evidence rows"
    assert all(item.metric_name == expected_metric for item in period_items)
    assert all(
        item.supporting_context.get("aggregation") == expected_aggregation
        for item in period_items
    )


def assert_run_analysis_complete(result: AnalysisResult) -> None:
    assert isinstance(result, AnalysisResult)
    assert result.clarification is None
    assert result.findings
    assert result.routes
    assert result.report is not None
    assert result.report.executive_summary
    assert result.direct_answer


def assert_answer_contains_standard_sections(answer: str) -> None:
    for heading in (
        "Direct Answer:",
        "Executive Summary:",
        "High Priority Findings:",
        "Medium Priority Findings:",
        "Low Priority Findings:",
        "Recommended Next Steps:",
        "Suggested Follow-Up Investigations:",
    ):
        assert heading in answer, f"Missing section heading: {heading}"


_CAUSATION_CLAIM_PHRASES = (
    "caused by",
    "because of",
    "due to",
    "root cause",
    "the reason is",
    "was caused",
)


def assert_no_causation_claims(text: str) -> None:
    """Guardrail: descriptive analytics must not assert causal explanations."""
    lowered = text.lower()
    for phrase in _CAUSATION_CLAIM_PHRASES:
        assert phrase not in lowered, f"Unexpected causation claim phrase: {phrase!r}"

_HUMILITY_VERBS = ("investigate", "review", "explore", "examine", "may warrant")

_SUGGESTION_CAUSATION_PHRASES = (
    "caused by",
    "because of",
    "due to",
    "proves",
    "responsible for",
    "root cause",
)


def assert_suggestions_are_humble(suggestions: list[str]) -> None:
    assert suggestions, "Expected at least one suggestion"
    for suggestion in suggestions:
        lowered = suggestion.lower()
        assert any(verb in lowered for verb in _HUMILITY_VERBS), (
            f"Suggestion missing humble wording: {suggestion!r}"
        )
        for phrase in _SUGGESTION_CAUSATION_PHRASES:
            assert phrase not in lowered, (
                f"Unexpected causation phrase {phrase!r} in suggestion: {suggestion!r}"
            )
