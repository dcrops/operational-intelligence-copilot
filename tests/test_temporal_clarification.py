"""Tests for temporal date-column clarification and request plumbing."""

from __future__ import annotations

import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.models import AnalysisRequest, DatasetProfile
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.temporal_resolution import (
    needs_date_column_clarification,
    resolve_date_column,
)
from tests.support.assertions import assert_clarification, assert_no_clarification
from tests.support.factories import manufacturing_bundle, workforce_bundle

pytestmark = pytest.mark.unit


def _multi_date_profile() -> DatasetProfile:
    return DatasetProfile(
        dataset_name="multi_date_demo",
        row_count=100,
        column_count=6,
        missing_value_count=0,
        column_names=["month", "report_date", "school", "attendance_rate"],
        numeric_columns=["attendance_rate"],
        categorical_columns=["school"],
        date_columns=["month", "report_date"],
        potential_metrics=["attendance_rate"],
        potential_dimensions=["school"],
        suitable_tools=["trend_analysis", "variance_analysis", "anomaly_detection"],
    )


class TestResolveDateColumn:
    def test_selected_date_column_is_preserved(self):
        request = AnalysisRequest(
            question="How has attendance changed in April 2026?",
            dataset_names=["multi_date_demo"],
            selected_date_column="report_date",
        )

        resolved = resolve_date_column(request, ["month", "report_date"])

        assert resolved == "report_date"

    def test_explicit_mention_resolves_without_selection(self):
        request = AnalysisRequest(
            question="How has attendance changed in April 2026 using report_date?",
            dataset_names=["multi_date_demo"],
        )

        resolved = resolve_date_column(request, ["month", "report_date"])

        assert resolved == "report_date"

    def test_single_date_column_auto_resolves(self):
        request = AnalysisRequest(
            question="How has attendance changed in April 2026?",
            dataset_names=["sample"],
        )

        resolved = resolve_date_column(request, ["month"])

        assert resolved == "month"

    def test_multiple_date_columns_without_selection_returns_none(self):
        request = AnalysisRequest(
            question="How has attendance changed in April 2026?",
            dataset_names=["multi_date_demo"],
        )

        resolved = resolve_date_column(request, ["month", "report_date"])

        assert resolved is None


class TestDateColumnClarificationDetection:
    def test_temporal_question_with_multiple_date_columns_requires_clarification(self):
        profile = _multi_date_profile()
        request = AnalysisRequest(
            question="How has attendance changed in April 2026?",
            dataset_names=[profile.dataset_name],
        )

        clarification = detect_clarification(
            request,
            ["trend_analysis"],
            profile,
        )

        assert_clarification(
            clarification,
            "date_column",
            options=["month", "report_date"],
        )

    def test_non_temporal_question_does_not_require_date_column_clarification(self):
        profile = _multi_date_profile()
        request = AnalysisRequest(
            question="Which school has the highest attendance?",
            dataset_names=[profile.dataset_name],
        )

        clarification = detect_clarification(
            request,
            ["variance_analysis"],
            profile,
        )

        assert clarification is None or clarification.clarification_type != "date_column"

    def test_selected_date_column_skips_date_column_clarification(self):
        profile = _multi_date_profile()
        request = AnalysisRequest(
            question="How has attendance changed in April 2026?",
            dataset_names=[profile.dataset_name],
            selected_date_column="month",
        )

        clarification = detect_clarification(
            request,
            ["trend_analysis"],
            profile,
        )

        assert clarification is None

    def test_single_date_column_does_not_require_date_column_clarification(self):
        df, profile = manufacturing_bundle()
        request = AnalysisRequest(
            question="How has defects changed in April 2026?",
            dataset_names=[profile.dataset_name],
        )

        assert len(profile.date_columns) == 1
        assert needs_date_column_clarification(request, profile.date_columns) is False

    def test_metric_clarification_still_takes_precedence(self):
        _, profile = manufacturing_bundle()
        profile = profile.model_copy(
            update={"date_columns": ["month", "report_date"]},
        )
        request = AnalysisRequest(
            question="How has performance changed in April 2026?",
            dataset_names=[profile.dataset_name],
        )

        clarification = detect_clarification(
            request,
            ["trend_analysis"],
            profile,
        )

        assert_clarification(clarification, "metric")


@pytest.mark.integration
def test_pipeline_returns_date_column_clarification_for_temporal_question():
    df, profile = manufacturing_bundle()
    profile = profile.model_copy(update={"date_columns": ["month", "report_date"]})
    request = AnalysisRequest(
        question="How has downtime changed in April 2026?",
        dataset_names=[profile.dataset_name],
    )

    outcome = OperationalPipeline().run(request, df, [profile])

    assert_clarification(
        outcome,
        "date_column",
        options=["month", "report_date"],
    )


@pytest.mark.integration
def test_pipeline_runs_after_date_column_selection():
    df, profile = manufacturing_bundle()
    profile = profile.model_copy(update={"date_columns": ["month", "report_date"]})
    request = AnalysisRequest(
        question="How has downtime changed in April 2026?",
        dataset_names=[profile.dataset_name],
        selected_date_column="month",
    )

    outcome = OperationalPipeline().run(request, df, [profile])

    assert_no_clarification(outcome)


@pytest.mark.integration
def test_existing_variance_clarification_behaviour_unchanged():
    _, profile = workforce_bundle()
    request = AnalysisRequest(
        question="Which group has the highest values?",
        dataset_names=[profile.dataset_name],
    )

    clarification = detect_clarification(
        request,
        ["variance_analysis"],
        profile,
    )

    assert_clarification(clarification, "metric")
