"""Tests for snapshot direct answers, transparency, and UI propagation."""

from __future__ import annotations

import pytest

from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest, SnapshotContext
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from src.operational_intelligence.snapshot_direct_answer import build_snapshot_direct_answer
from ui.analysis_service import run_analysis
from ui.transparency import format_snapshot_trail, format_temporal_filter_trail
from tests.support.assertions import (
    assert_no_clarification,
    pipeline_snapshot_context,
    pipeline_temporal_filter,
)
from tests.support.builders import make_snapshot_finding
from tests.support.factories import manufacturing_bundle

pytestmark = pytest.mark.unit


class TestSnapshotDirectAnswer:
    def test_snapshot_answer_uses_period_and_baseline_from_evidence(self):
        finding = make_snapshot_finding()

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Attendance rate in April 2026 was 88.23, above the dataset "
            "average of 86.98 (+1.25 above baseline)."
        )

    def test_snapshot_answer_broadly_in_line_when_delta_is_small(self):
        finding = make_snapshot_finding(
            baseline_value=88.28,
            delta_vs_baseline=-0.05,
        )

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Attendance rate in April 2026 was 88.23, broadly in line with "
            "the dataset average of 88.28."
        )

    def test_snapshot_answer_above_baseline_when_delta_is_meaningfully_positive(self):
        finding = make_snapshot_finding(
            metric_name="defects",
            period_value=52.0,
            baseline_value=8.22,
            delta_vs_baseline=43.78,
        )

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Defects in April 2026 was 52, above the dataset average of 8.22 "
            "(+43.78 above baseline)."
        )

    def test_snapshot_answer_below_baseline_when_delta_is_meaningfully_negative(self):
        finding = make_snapshot_finding(
            period_value=80.0,
            baseline_value=90.0,
            delta_vs_baseline=-10.0,
        )

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Attendance rate in April 2026 was 80, below the dataset average "
            "of 90 (-10 below baseline)."
        )

    def test_snapshot_answer_without_delta_metadata(self):
        finding = make_snapshot_finding(delta_vs_baseline=0.0)

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Attendance rate in April 2026 was 88.23, broadly in line with "
            "the dataset average of 86.98."
        )

    def test_snapshot_answer_avoids_trend_language(self):
        finding = make_snapshot_finding()
        answer = build_snapshot_direct_answer(finding)

        assert answer is not None
        lowered = answer.lower()
        for forbidden in ("trend", "stable", "changed", "0%"):
            assert forbidden not in lowered

    def test_answer_generator_prefers_snapshot_direct_answer(self):
        finding = make_snapshot_finding()
        report = ExecutiveReportGenerator().generate([finding])

        direct = AnswerGenerator()._build_direct_answer(
            AnalysisRequest(
                question="How has attendance changed in April 2026?",
                dataset_names=["education_synthetic"],
            ),
            [finding],
            report,
        )

        assert "above the dataset average" in direct
        assert "remained stable" not in direct.lower()


class TestSnapshotTransparency:
    def test_format_snapshot_trail_returns_period_reason_and_analysis(self):
        lines = format_snapshot_trail(
            SnapshotContext(
                activated=True,
                reason="Only one temporal period remained in the scoped dataset.",
                period_label="April 2026",
                bucket_count=1,
            )
        )

        assert lines == [
            "Period: April 2026",
            "Reason: Only one temporal period remained in the scoped dataset.",
            "Analysis: Snapshot Intelligence",
        ]

    def test_format_snapshot_trail_empty_when_not_activated(self):
        assert format_snapshot_trail(None) == []


@pytest.mark.integration
class TestSnapshotPresentationPropagation:
    def test_run_analysis_carries_snapshot_context_from_pipeline(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has defects changed in April 2026?",
            df,
            profile,
        )

        assert result.clarification is None
        assert result.snapshot_context is not None
        assert result.snapshot_context.activated is True
        assert result.snapshot_context.period_label == "April 2026"

    def test_snapshot_direct_answer_from_analysis_service(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has defects changed in April 2026?",
            df,
            profile,
        )

        assert result.direct_answer
        lowered = result.direct_answer.lower()
        assert "trend" not in lowered
        assert "stable" not in lowered
        assert "0%" not in lowered
        assert "changed" not in lowered
        assert "April 2026" in result.direct_answer
        assert "dataset average" in result.direct_answer

    def test_snapshot_and_temporal_transparency_metadata_both_available(self):
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
        assert pipeline_temporal_filter(outcome) is not None
        assert pipeline_snapshot_context(outcome) is not None
        assert format_temporal_filter_trail(pipeline_temporal_filter(outcome))
        assert format_snapshot_trail(pipeline_snapshot_context(outcome))

    def test_non_snapshot_analysis_has_no_snapshot_transparency(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has defects changed over time?",
            df,
            profile,
        )

        assert result.snapshot_context is None
        assert format_snapshot_trail(result.snapshot_context) == []
