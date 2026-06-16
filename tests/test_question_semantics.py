import pytest

from src.operational_intelligence.question_semantics import (
    DEFAULT_AGGREGATION,
    has_conflicting_comparison_direction,
    infer_aggregation_type,
    is_dual_comparison_question,
    question_uses_broad_metric_term,
    resolve_comparison_direction,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Which school has the highest attendance?", "top"),
        ("Which school has the lowest attendance?", "bottom"),
        ("Which school has the highest and lowest attendance?", "dual"),
        ("Which department has the best and worst hours?", "dual"),
        ("Which group is highest or lowest?", None),
    ],
)
def test_resolve_comparison_direction(question: str, expected: str | None):
    assert resolve_comparison_direction(question) == expected


def test_dual_comparison_is_not_treated_as_conflict():
    question = "Which production line has the highest and lowest defects?"
    assert is_dual_comparison_question(question) is True
    assert has_conflicting_comparison_direction(question) is False
    assert resolve_comparison_direction(question) == "dual"


def test_conflicting_direction_without_dual_cue():
    question = "Is school A highest or lowest?"
    assert is_dual_comparison_question(question) is False
    assert has_conflicting_comparison_direction(question) is True
    assert resolve_comparison_direction(question) is None


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("attendance_rate", "mean"),
        ("average_score", "mean"),
        ("defects", DEFAULT_AGGREGATION),
        ("behaviour_incidents", DEFAULT_AGGREGATION),
        ("downtime_minutes", DEFAULT_AGGREGATION),
        ("hours", DEFAULT_AGGREGATION),
    ],
)
def test_infer_aggregation_type(metric: str, expected: str):
    assert infer_aggregation_type(metric) == expected


def test_broad_metric_term_detection():
    assert question_uses_broad_metric_term("How has performance changed?") is True
    assert question_uses_broad_metric_term("How has attendance changed?") is False
