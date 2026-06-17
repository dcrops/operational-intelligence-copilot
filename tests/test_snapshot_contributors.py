"""Tests for snapshot contributor analysis and presentation."""

from __future__ import annotations

import pytest

from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from src.operational_intelligence.snapshot_analysis import extract_snapshot_contributors
from src.operational_intelligence.snapshot_direct_answer import build_snapshot_direct_answer
from ui.analysis_service import run_analysis
from ui.transparency import format_snapshot_contributors_trail
from tests.support.builders import make_snapshot_finding
from tests.support.factories import manufacturing_bundle

pytestmark = pytest.mark.unit


class TestSnapshotContributorDirectAnswer:
    def test_contributor_formatting_appended_to_snapshot_answer(self):
        finding = make_snapshot_finding(
            delta_vs_baseline=-0.05,
            dimension_name="school",
            highest_entity="School A",
            highest_value=95.2,
            lowest_entity="School D",
            lowest_value=72.1,
        )

        answer = build_snapshot_direct_answer(finding)

        assert answer is not None
        assert (
            "Attendance rate in April 2026 was 88.23, broadly in line with "
            "the dataset average of 86.98." in answer
        )
        assert "Highest contributor:\nSchool A (95.2)" in answer
        assert "Lowest contributor:\nSchool D (72.1)" in answer

    def test_no_contributor_fallback_preserves_existing_answer(self):
        finding = make_snapshot_finding()

        answer = build_snapshot_direct_answer(finding)

        assert answer == (
            "Attendance rate in April 2026 was 88.23, above the dataset "
            "average of 86.98 (+1.25 above baseline)."
        )


class TestSnapshotContributorTransparency:
    def test_format_snapshot_contributors_trail_renders_dimension_highest_lowest(self):
        finding = make_snapshot_finding(
            dimension_name="school",
            highest_entity="School A",
            highest_value=95.2,
            lowest_entity="School D",
            lowest_value=72.1,
        )

        lines = format_snapshot_contributors_trail([finding])

        assert lines == [
            "Dimension: school",
            "Highest: School A (95.2)",
            "Lowest: School D (72.1)",
        ]

    def test_format_snapshot_contributors_trail_empty_when_absent(self):
        assert format_snapshot_contributors_trail([make_snapshot_finding()]) == []


@pytest.mark.integration
class TestSnapshotContributorIntegration:
    def test_run_analysis_includes_contributors_when_dimension_resolves(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "How has defects changed in April 2026?",
            df,
            profile,
            selected_dimensions=["production_line"],
        )

        assert result.findings
        contributors = extract_snapshot_contributors(result.findings[0])
        assert contributors is not None
        dimension_name, highest, lowest = contributors
        assert dimension_name == "production_line"
        assert highest.entity_name == "Line B"
        assert lowest.entity_name == "Line A"
        assert "Highest contributor:" in result.direct_answer
        assert "Line B" in result.direct_answer
        assert format_snapshot_contributors_trail(result.findings)

    def test_answer_generator_prefers_snapshot_contributor_answer(self):
        finding = make_snapshot_finding(
            dimension_name="production_line",
            highest_entity="Line B",
            highest_value=8.0,
            lowest_entity="Line A",
            lowest_value=2.0,
        )
        report = ExecutiveReportGenerator().generate([finding])

        direct = AnswerGenerator()._build_direct_answer(
            AnalysisRequest(
                question="How has defects changed in April 2026?",
                dataset_names=["manufacturing_synthetic"],
                selected_dimensions=["production_line"],
            ),
            [finding],
            report,
        )

        assert "Highest contributor:" in direct
        assert "Lowest contributor:" in direct
