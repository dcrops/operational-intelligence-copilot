"""Tests for temporal filter transparency from pipeline through UI formatters."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.operational_intelligence.models import AnalysisRequest, PipelineAnalysisResult
from src.operational_intelligence.pipeline import OperationalPipeline
from ui.analysis_service import run_analysis
from ui.transparency import format_temporal_filter_trail
from tests.support.assertions import (
    assert_no_clarification,
    pipeline_findings,
    pipeline_temporal_filter,
)
from tests.support.factories import manufacturing_bundle

pytestmark = pytest.mark.integration


class TestTemporalFilterContext:
    def test_temporal_filter_context_row_count_matches_filtered_dataset(self):
        df, profile = manufacturing_bundle()
        apply_calls: list[int] = []

        original_apply = __import__(
            "src.operational_intelligence.temporal_resolution",
            fromlist=["apply_temporal_filter"],
        ).apply_temporal_filter

        def counting_apply(source_df, date_column, constraint):
            filtered = original_apply(source_df, date_column, constraint)
            apply_calls.append(len(filtered))
            return filtered

        with patch(
            "src.operational_intelligence.pipeline.apply_temporal_filter",
            side_effect=counting_apply,
        ):
            outcome = OperationalPipeline().run(
                AnalysisRequest(
                    question="Which production line has the highest defects in Q1 2026?",
                    dataset_names=[profile.dataset_name],
                ),
                df,
                [profile],
            )

        assert_no_clarification(outcome)
        temporal_filter = pipeline_temporal_filter(outcome)
        assert temporal_filter is not None
        assert len(apply_calls) == 1
        assert temporal_filter.filtered_row_count == apply_calls[0]
        assert temporal_filter.filtered_row_count == 6

    def test_temporal_filter_context_populated_after_filtering(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="Which production line has the highest defects in Q1 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert isinstance(outcome, PipelineAnalysisResult)
        temporal_filter = pipeline_temporal_filter(outcome)
        assert temporal_filter is not None
        assert temporal_filter.label == "Q1 2026"
        assert temporal_filter.date_column == "month"
        assert temporal_filter.original_row_count == len(df)
        assert temporal_filter.filtered_row_count == 6
        assert temporal_filter.date_column_inferred is True

    def test_temporal_filter_context_absent_for_non_temporal_questions(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="Which production line has the highest defects?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert pipeline_temporal_filter(outcome) is None

    def test_empty_temporal_filter_still_exposes_context(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed in December 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        temporal_filter = pipeline_temporal_filter(outcome)
        assert temporal_filter is not None
        assert temporal_filter.label == "December 2026"
        assert temporal_filter.filtered_row_count == 0
        assert temporal_filter.original_row_count == len(df)
        assert pipeline_findings(outcome) == []


class TestTemporalTransparencyFormatter:
    def test_format_temporal_filter_trail_shows_period_date_column_and_counts(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="Which production line has the highest defects in Q1 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        lines = format_temporal_filter_trail(pipeline_temporal_filter(outcome))

        assert lines == [
            "Period: Q1 2026",
            "Date column: month",
            f"Records analysed: 6 of {len(df)}",
            "Date column inferred: month",
        ]

    def test_format_temporal_filter_trail_empty_when_no_filter(self):
        assert format_temporal_filter_trail(None) == []


class TestAnalysisServiceTemporalPropagation:
    def test_run_analysis_carries_pipeline_temporal_filter_without_reparse(self):
        df, profile = manufacturing_bundle()
        question = "Which production line has the highest defects in Q1 2026?"

        with patch(
            "src.operational_intelligence.temporal_resolution.parse_temporal_constraint",
            wraps=__import__(
                "src.operational_intelligence.temporal_resolution",
                fromlist=["parse_temporal_constraint"],
            ).parse_temporal_constraint,
        ) as parse_mock:
            result = run_analysis(question, df, profile)

        assert result.clarification is None
        assert result.temporal_filter is not None
        assert result.temporal_filter.label == "Q1 2026"
        assert result.temporal_filter.filtered_row_count == 6
        assert result.temporal_filter.original_row_count == len(df)
        parse_mock.assert_called_once_with(question)

    def test_run_analysis_has_no_temporal_filter_for_non_temporal_question(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )

        assert result.temporal_filter is None
