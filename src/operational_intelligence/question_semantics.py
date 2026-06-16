"""Deterministic question semantics: comparison direction, aggregation, and intent signals."""

from __future__ import annotations

import re
from typing import Literal

ComparisonDirection = Literal["top", "bottom", "dual"]
AggregationType = Literal["mean", "sum"]

DEFAULT_AGGREGATION: AggregationType = "sum"

TOP_TERMS = (
    "highest",
    "most",
    "largest",
    "greatest",
    "maximum",
    "best",
    "top",
)
BOTTOM_TERMS = (
    "lowest",
    "least",
    "smallest",
    "minimum",
    "worst",
    "poorest",
    "bottom",
)
COMPARATIVE_TERMS = TOP_TERMS + BOTTOM_TERMS + (
    "compare",
    "difference",
    "variance",
    "performing",
)
ANOMALY_TERMS = (
    "anomaly",
    "unusual",
    "outlier",
    "abnormal",
    "suspicious",
    "spike",
)
TREND_TERMS = (
    "trend",
    "over time",
    "changed",
    "increase",
    "decrease",
    "monthly",
    "weekly",
)
RISK_TERMS = (
    "risk",
    "investigate",
    "concern",
    "issue",
    "problem",
    "review",
)
BROAD_METRIC_TERMS = (
    "performance",
    "results",
    "outcome",
    "output",
    "activity",
)
RATE_TOKENS = ("rate", "percentage", "percent", "ratio", "pct")
MEAN_TOKENS = ("score", "average", "avg", "mean")
DUAL_COMPARISON_CUES = (" and ", " vs ", " versus ")
CAUSATION_PHRASES = (
    "what caused",
    "cause of",
    "driver of",
    "drivers of",
    "reason for",
    "what led to",
    "what contributed to",
)
CAUSATION_DISCLAIMER = (
    "I cannot determine causation from this dataset alone. The current analysis "
    "capabilities identify trends, anomalies, and differences, but do not establish "
    "causal relationships."
)
CAUSATION_FINDINGS_INTRO = (
    "However, the following findings may warrant further investigation:"
)


def _contains_term(question_lower: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", question_lower) is not None


def _matched_terms(question_lower: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if _contains_term(question_lower, term)]


def has_comparative_intent(question: str) -> bool:
    question_lower = question.lower()
    return any(_contains_term(question_lower, term) for term in COMPARATIVE_TERMS)


def has_anomaly_intent(question: str) -> bool:
    question_lower = question.lower()
    return any(_contains_term(question_lower, term) for term in ANOMALY_TERMS)


def has_trend_intent(question: str) -> bool:
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in TREND_TERMS)


def has_risk_intent(question: str) -> bool:
    question_lower = question.lower()
    return any(_contains_term(question_lower, term) for term in RISK_TERMS)


def causation_requested(question: str) -> bool:
    """Return True when the question asks for causal attribution."""
    question_lower = question.lower().strip()
    if _contains_term(question_lower, "why"):
        return True
    return any(phrase in question_lower for phrase in CAUSATION_PHRASES)


def is_comparative_question(question: str) -> bool:
    return has_comparative_intent(question)


def is_dual_comparison_question(question: str) -> bool:
    question_lower = question.lower()
    top_terms = _matched_terms(question_lower, TOP_TERMS)
    bottom_terms = _matched_terms(question_lower, BOTTOM_TERMS)
    if not top_terms or not bottom_terms:
        return False

    if any(cue in question_lower for cue in DUAL_COMPARISON_CUES):
        return True

    paired_patterns = (
        r"\bhighest\s+and\s+lowest\b",
        r"\bbest\s+and\s+worst\b",
        r"\btop\s+and\s+bottom\b",
        r"\bmost\s+and\s+least\b",
        r"\bmaximum\s+and\s+minimum\b",
        r"\blargest\s+and\s+smallest\b",
        r"\bgreatest\s+and\s+poorest\b",
    )
    return any(re.search(pattern, question_lower) for pattern in paired_patterns)


def has_conflicting_comparison_direction(question: str) -> bool:
    question_lower = question.lower()
    has_top = bool(_matched_terms(question_lower, TOP_TERMS))
    has_bottom = bool(_matched_terms(question_lower, BOTTOM_TERMS))
    return has_top and has_bottom and not is_dual_comparison_question(question)


def resolve_comparison_direction(question: str) -> ComparisonDirection | None:
    if is_dual_comparison_question(question):
        return "dual"

    question_lower = question.lower()
    top_terms = _matched_terms(question_lower, TOP_TERMS)
    bottom_terms = _matched_terms(question_lower, BOTTOM_TERMS)

    if top_terms and bottom_terms:
        return None
    if top_terms:
        return "top"
    if bottom_terms:
        return "bottom"
    return None


def infer_aggregation_type(metric_column: str) -> AggregationType:
    normalized = metric_column.strip().lower().replace("_", " ")
    tokens = normalized.split()

    if any(token in RATE_TOKENS for token in tokens) or any(
        token.endswith(suffix)
        for token in tokens
        for suffix in ("rate", "ratio", "percent", "percentage", "pct")
    ):
        return "mean"

    if any(token in MEAN_TOKENS for token in tokens):
        return "mean"

    return DEFAULT_AGGREGATION


def question_uses_broad_metric_term(question: str) -> bool:
    question_lower = question.lower()
    return any(_contains_term(question_lower, term) for term in BROAD_METRIC_TERMS)


def has_explicit_column_mention(question: str, column_name: str) -> bool:
    question_lower = question.lower()
    column_lower = column_name.strip().lower()
    spaced = column_lower.replace("_", " ")
    return column_lower in question_lower or spaced in question_lower


def requests_dual_analysis_outcomes(question: str) -> bool:
    question_lower = question.lower()
    dual_phrases = (
        "compare and find unusual",
        "compare and detect unusual",
        "variance and anomaly",
        "comparison and anomaly",
        "compare and investigate unusual",
    )
    return any(phrase in question_lower for phrase in dual_phrases)


def aggregation_label(aggregation: AggregationType) -> str:
    return "mean" if aggregation == "mean" else "total"
