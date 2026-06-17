"""Integration tests for snapshot mode inside OperationalPipeline."""

from __future__ import annotations

import pytest

from src.operational_intelligence.models import AnalysisRequest, PipelineAnalysisResult
from src.operational_intelligence.pipeline import OperationalPipeline
from tests.support.assertions import (
    assert_no_clarification,
    assert_trend_outcome,
    assert_variance_outcome,
    pipeline_findings,
    pipeline_snapshot_context,
)
from tests.support.factories import (
    MANUFACTURING_HIGHEST_DEFECTS_LINE,
    manufacturing_bundle,
)

pytestmark = pytest.mark.integration


def _finding_titles(result) -> list[str]:
    return [finding.title for finding in pipeline_findings(result)]


def _trend_n_periods(result) -> int | None:
    for finding in pipeline_findings(result):
        if "trend" not in finding.title.lower():
            continue
        for item in finding.evidence:
            n_periods = item.supporting_context.get("n_periods")
            if n_periods is not None:
                return int(n_periods)
    return None


class TestSnapshotPipelineIntegration:
    def test_april_trend_question_activates_snapshot_mode(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed in April 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert isinstance(outcome, PipelineAnalysisResult)

        snapshot = pipeline_snapshot_context(outcome)
        assert snapshot is not None
        assert snapshot.activated is True
        assert snapshot.bucket_count == 1
        assert snapshot.period_label == "April 2026"

        titles = _finding_titles(outcome)
        assert any("Snapshot Summary" in title for title in titles)
        assert not any("Trend Identified" in title for title in titles)
        assert _trend_n_periods(outcome) is None

    def test_q1_trend_question_remains_trend_analysis(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed in Q1 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert pipeline_snapshot_context(outcome) is None
        assert _trend_n_periods(outcome) == 3
        assert_trend_outcome(
            outcome,
            expected_metric="defects",
            expected_aggregation="sum",
        )

    def test_non_temporal_trend_question_remains_trend_analysis(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed over time?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert pipeline_snapshot_context(outcome) is None
        assert _trend_n_periods(outcome) == 4

    def test_variance_question_never_activates_snapshot_mode(self):
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
        assert pipeline_snapshot_context(outcome) is None
        assert_variance_outcome(
            outcome,
            expected_metric="defects",
            expected_dimension="production_line",
            expected_aggregation="sum",
            expected_direction="top",
            expected_targets=[MANUFACTURING_HIGHEST_DEFECTS_LINE],
        )

    def test_anomaly_question_never_activates_snapshot_mode(self):
        df, profile = manufacturing_bundle()
        outcome = OperationalPipeline().run(
            AnalysisRequest(
                question="What looks unusual in January 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(outcome)
        assert pipeline_snapshot_context(outcome) is None
        assert not any("Snapshot Summary" in title for title in _finding_titles(outcome))
