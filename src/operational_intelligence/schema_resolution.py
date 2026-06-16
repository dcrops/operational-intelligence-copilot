"""Deterministic schema-aware metric and dimension resolution from natural language questions."""

from __future__ import annotations

import re

from src.operational_intelligence.question_semantics import (
    has_explicit_column_mention,
    question_uses_broad_metric_term,
)

IDENTIFIER_COLUMNS = {
    "employee_id",
    "employee_number",
    "record_id",
    "transaction_id",
    "id",
    "uuid",
}


def is_identifier_column(column_name: str) -> bool:
    name = column_name.strip()
    lowered = name.lower()
    if lowered in IDENTIFIER_COLUMNS:
        return True
    if (
        lowered.endswith("_id")
        or lowered.endswith("_number")
        or lowered.endswith("_no")
    ):
        return True
    # camelCase account/order number columns (e.g. accountNo, invoiceNo)
    if re.search(r"[a-z]No$", name):
        return True
    return False


def non_identifier_dimensions(candidate_dimensions: list[str]) -> list[str]:
    return [
        dimension
        for dimension in candidate_dimensions
        if not is_identifier_column(dimension)
    ]


def _question_mentions_column(
    question: str,
    column_name: str,
    *,
    allow_partial: bool = True,
) -> bool:
    question_lower = question.lower()
    column_lower = column_name.strip().lower()
    spaced = column_lower.replace("_", " ")

    if column_lower in question_lower:
        return True
    if spaced in question_lower:
        return True

    if not allow_partial or "_" not in column_lower:
        return False

    first_token = column_lower.split("_", 1)[0]
    if not first_token:
        return False

    return re.search(rf"\b{re.escape(first_token)}\b", question_lower) is not None


def resolve_metric_from_question(
    question: str,
    candidate_metrics: list[str],
) -> str | None:
    explicit_matches = [
        metric
        for metric in candidate_metrics
        if has_explicit_column_mention(question, metric)
    ]
    if explicit_matches:
        return max(explicit_matches, key=len)

    if question_uses_broad_metric_term(question):
        return None

    matched = [
        metric
        for metric in candidate_metrics
        if _question_mentions_column(question, metric, allow_partial=True)
    ]
    if not matched:
        return None
    return max(matched, key=len)


def resolve_dimension_from_question(
    question: str,
    candidate_dimensions: list[str],
) -> str | None:
    matched: list[str] = []

    for dimension in candidate_dimensions:
        if is_identifier_column(dimension):
            if _question_mentions_column(question, dimension, allow_partial=False):
                matched.append(dimension)
            continue

        if _question_mentions_column(question, dimension, allow_partial=True):
            matched.append(dimension)

    if not matched:
        return None
    return max(matched, key=len)


def select_variance_dimension(
    question: str,
    candidate_dimensions: list[str],
) -> str:
    explicit_dimension = resolve_dimension_from_question(question, candidate_dimensions)
    if explicit_dimension is not None:
        return explicit_dimension

    fallback_dimensions = non_identifier_dimensions(candidate_dimensions)
    if fallback_dimensions:
        return fallback_dimensions[0]

    return candidate_dimensions[0]
