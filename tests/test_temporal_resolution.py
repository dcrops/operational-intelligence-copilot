"""Unit tests for temporal constraint parsing and filtering."""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.temporal_resolution import (
    TemporalConstraintKind,
    apply_temporal_filter,
    parse_temporal_constraint,
)

pytestmark = pytest.mark.unit


class TestParseTemporalConstraint:
    def test_month_and_year(self):
        constraint = parse_temporal_constraint(
            "How has attendance changed in April 2026?"
        )

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.MONTH_YEAR
        assert constraint.label == "April 2026"
        assert constraint.start == pd.Timestamp("2026-04-01")
        assert constraint.end == pd.Timestamp("2026-05-01")

    def test_month_and_year_march(self):
        constraint = parse_temporal_constraint(
            "Which school had the lowest attendance in March 2026?"
        )

        assert constraint is not None
        assert constraint.label == "March 2026"
        assert constraint.start == pd.Timestamp("2026-03-01")
        assert constraint.end == pd.Timestamp("2026-04-01")

    def test_month_only(self):
        constraint = parse_temporal_constraint("What looked unusual in January?")

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.MONTH_ONLY
        assert constraint.label == "January"
        assert constraint.calendar_month == 1
        assert constraint.start is None
        assert constraint.end is None

    def test_year_only(self):
        constraint = parse_temporal_constraint("How has performance changed in 2026?")

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.YEAR
        assert constraint.label == "2026"
        assert constraint.start == pd.Timestamp("2026-01-01")
        assert constraint.end == pd.Timestamp("2027-01-01")

    def test_quarter_q1(self):
        constraint = parse_temporal_constraint(
            "Which school had the lowest attendance in Q1 2026?"
        )

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.QUARTER
        assert constraint.label == "Q1 2026"
        assert constraint.start == pd.Timestamp("2026-01-01")
        assert constraint.end == pd.Timestamp("2026-04-01")

    def test_quarter_q2(self):
        constraint = parse_temporal_constraint("Summarise anomalies in Q2 2025")

        assert constraint is not None
        assert constraint.label == "Q2 2025"
        assert constraint.start == pd.Timestamp("2025-04-01")
        assert constraint.end == pd.Timestamp("2025-07-01")

    def test_quarter_spelled_out(self):
        constraint = parse_temporal_constraint(
            "What looked unusual in Quarter 3 2026?"
        )

        assert constraint is not None
        assert constraint.label == "Q3 2026"
        assert constraint.start == pd.Timestamp("2026-07-01")
        assert constraint.end == pd.Timestamp("2026-10-01")

    @pytest.mark.parametrize(
        "question",
        [
            "What looks unusual this month?",
            "How have hours changed last month?",
            "Compare April to May in 2026",
            "How has attendance changed since March?",
            "What happened after April 2026?",
        ],
    )
    def test_out_of_scope_patterns_return_none(self, question: str):
        assert parse_temporal_constraint(question) is None

    def test_empty_question_returns_none(self):
        assert parse_temporal_constraint("") is None
        assert parse_temporal_constraint("   ") is None

    def test_non_temporal_question_returns_none(self):
        assert parse_temporal_constraint("Which department has the highest hours?") is None

    def test_month_year_takes_precedence_over_year_only(self):
        constraint = parse_temporal_constraint("Review attendance in April 2026")

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.MONTH_YEAR

    def test_quarter_takes_precedence_over_year_only(self):
        constraint = parse_temporal_constraint("Review attendance in Q1 2026")

        assert constraint is not None
        assert constraint.kind is TemporalConstraintKind.QUARTER


class TestApplyTemporalFilter:
    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "month": [
                    "2026-01-01",
                    "2026-02-01",
                    "2026-03-01",
                    "2026-04-01",
                    "2025-01-01",
                    "2025-04-01",
                ],
                "school": ["A", "A", "A", "A", "B", "B"],
                "attendance_rate": [90.0, 91.0, 92.0, 51.0, 88.0, 89.0],
            }
        )

    def test_filters_month_and_year(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("What happened in April 2026?")
        assert constraint is not None

        filtered = apply_temporal_filter(sample_df, "month", constraint)

        assert len(filtered) == 1
        assert filtered.iloc[0]["attendance_rate"] == 51.0

    def test_filters_quarter(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("Review Q1 2026")
        assert constraint is not None

        filtered = apply_temporal_filter(sample_df, "month", constraint)

        assert len(filtered) == 3
        assert set(filtered["month"].tolist()) == {
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        }

    def test_filters_year_only(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("Review 2026")
        assert constraint is not None

        filtered = apply_temporal_filter(sample_df, "month", constraint)

        assert len(filtered) == 4
        assert all(str(value).startswith("2026") for value in filtered["month"])

    def test_filters_month_only_across_years(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("What looked unusual in January?")
        assert constraint is not None

        filtered = apply_temporal_filter(sample_df, "month", constraint)

        assert len(filtered) == 2
        assert set(filtered["month"].tolist()) == {"2026-01-01", "2025-01-01"}

    def test_empty_result_when_no_matching_rows(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("Review December 2026")
        assert constraint is not None

        filtered = apply_temporal_filter(sample_df, "month", constraint)

        assert filtered.empty
        assert list(filtered.columns) == list(sample_df.columns)

    def test_invalid_date_column_raises(self, sample_df: pd.DataFrame):
        constraint = parse_temporal_constraint("Review April 2026")
        assert constraint is not None

        with pytest.raises(ValueError, match="date_column 'missing' not found"):
            apply_temporal_filter(sample_df, "missing", constraint)

    def test_unparseable_dates_are_excluded(self):
        df = pd.DataFrame(
            {
                "month": ["2026-04-01", "not-a-date", "2026-04-15"],
                "value": [1, 2, 3],
            }
        )
        constraint = parse_temporal_constraint("Review April 2026")
        assert constraint is not None

        filtered = apply_temporal_filter(df, "month", constraint)

        assert len(filtered) == 2
        assert filtered["value"].tolist() == [1, 3]
