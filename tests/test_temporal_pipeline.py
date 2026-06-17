"""Integration tests for temporal filtering inside OperationalPipeline."""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.models import AnalysisRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from tests.support.assertions import (
    assert_no_clarification,
    assert_variance_outcome,
    pipeline_findings,
    pipeline_temporal_filter,
)
from tests.support.factories import (
    MANUFACTURING_HIGHEST_DEFECTS_LINE,
    manufacturing_bundle,
)

pytestmark = pytest.mark.integration


def _trend_n_periods(findings) -> int | None:
    findings = pipeline_findings(findings)
    for finding in findings:
        if "trend" not in finding.title.lower():
            continue
        for item in finding.evidence:
            n_periods = item.supporting_context.get("n_periods")
            if n_periods is not None:
                return int(n_periods)
    return None


def _anomaly_evidence_count(findings) -> int:
    findings = pipeline_findings(findings)
    return sum(
        len(finding.evidence)
        for finding in findings
        if "anomaly" in finding.title.lower()
    )


class TestTemporalPipelineFiltering:
    def test_temporal_filter_applied_before_trend_analysis(self):
        df, profile = manufacturing_bundle()
        pipeline = OperationalPipeline()

        full_findings = pipeline.run(
            AnalysisRequest(
                question="How has defects changed over time?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )
        april_findings = pipeline.run(
            AnalysisRequest(
                question="How has defects changed in April 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(full_findings)
        assert_no_clarification(april_findings)
        assert _trend_n_periods(full_findings) == 4
        assert _trend_n_periods(april_findings) == 1

    def test_temporal_filter_applied_before_variance_analysis(self):
        df, profile = manufacturing_bundle()
        df = df.copy()
        df.loc[pd.to_datetime(df["month"]) == pd.Timestamp("2026-04-01"), "defects"] = 999

        pipeline = OperationalPipeline()
        findings = pipeline.run(
            AnalysisRequest(
                question="Which production line has the highest defects in Q1 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(findings)
        assert_variance_outcome(
            findings,
            expected_metric="defects",
            expected_dimension="production_line",
            expected_aggregation="sum",
            expected_direction="top",
            expected_targets=[MANUFACTURING_HIGHEST_DEFECTS_LINE],
        )

    def test_temporal_filter_applied_before_anomaly_detection(self):
        df, profile = manufacturing_bundle()
        pipeline = OperationalPipeline()

        full_findings = pipeline.run(
            AnalysisRequest(
                question="What looks unusual?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )
        january_findings = pipeline.run(
            AnalysisRequest(
                question="What looks unusual in January 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(full_findings)
        assert_no_clarification(january_findings)
        assert _anomaly_evidence_count(full_findings) >= 1
        assert _anomaly_evidence_count(january_findings) == 0

    def test_non_temporal_questions_behave_as_before(self):
        df, profile = manufacturing_bundle()
        findings = OperationalPipeline().run(
            AnalysisRequest(
                question="Which production line has the highest defects?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(findings)
        assert_variance_outcome(
            findings,
            expected_metric="defects",
            expected_dimension="production_line",
            expected_aggregation="sum",
            expected_direction="top",
            expected_targets=[MANUFACTURING_HIGHEST_DEFECTS_LINE],
        )

    def test_empty_temporal_filter_returns_no_findings(self):
        df, profile = manufacturing_bundle()
        findings = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed in December 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert_no_clarification(findings)
        assert pipeline_findings(findings) == []
        assert pipeline_temporal_filter(findings) is not None
        assert pipeline_temporal_filter(findings).filtered_row_count == 0

    def test_temporal_question_without_date_columns_returns_no_findings(self):
        df, profile = manufacturing_bundle()
        profile = profile.model_copy(update={"date_columns": []})
        findings = OperationalPipeline().run(
            AnalysisRequest(
                question="How has defects changed in April 2026?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert pipeline_findings(findings) == []
        assert pipeline_temporal_filter(findings) is None
