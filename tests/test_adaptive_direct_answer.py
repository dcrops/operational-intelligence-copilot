"""Unit tests for adaptive anomaly Direct Answer formatting."""

import pytest

from src.operational_intelligence.anomaly_direct_answer import build_anomaly_direct_answer
from tests.support.builders import (
    make_anomaly_evidence_item,
    make_anomaly_evidence_items,
    make_anomaly_finding_with_evidence,
)


@pytest.mark.unit
class TestAdaptiveAnomalyDirectAnswer:
    def test_single_anomaly_lists_one_affected_record(self):
        finding = make_anomaly_finding_with_evidence(
            [make_anomaly_evidence_item(row_index=126, metric_value=52.0)]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Affected records:" in answer
        assert answer.count("- Row ") == 1
        assert "Row 126" in answer

    def test_five_anomalies_lists_all_rows(self):
        evidence = make_anomaly_evidence_items(5, start_row_index=10)
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Affected records:" in answer
        assert answer.count("- Row ") == 5
        assert "Examples include:" not in answer

    def test_six_anomalies_shows_three_examples_and_three_additional(self):
        evidence = make_anomaly_evidence_items(6, start_row_index=1)
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Examples include:" in answer
        assert answer.count("- Row ") == 3
        assert "3 additional anomalous records were also identified." in answer
        assert "Affected records:" not in answer

    def test_twenty_anomalies_shows_three_examples_and_seventeen_additional(self):
        evidence = make_anomaly_evidence_items(20, start_row_index=1)
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert answer.count("- Row ") == 3
        assert "17 additional anomalous records were also identified." in answer

    def test_twenty_one_anomalies_uses_evidence_pointer_only(self):
        evidence = make_anomaly_evidence_items(21, start_row_index=1)
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Affected records:" not in answer
        assert "Examples include:" not in answer
        assert "- Row " not in answer
        assert (
            "See supporting evidence for the complete list of affected records."
            in answer
        )

    def test_high_direction_appears_in_header(self):
        evidence = make_anomaly_evidence_items(3, anomaly_direction="HIGH")
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "unusual HIGH values were detected" in answer

    def test_low_direction_uses_lowest_observed_in_medium_tier(self):
        evidence = make_anomaly_evidence_items(
            8,
            anomaly_direction="LOW",
            start_metric_value=2.0,
        )
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "unusual LOW values were detected" in answer
        assert "The lowest observed value was 2." in answer

    def test_record_lines_use_evidence_metric_values(self):
        evidence = [
            make_anomaly_evidence_item(row_index=1, metric_value=11.5),
            make_anomaly_evidence_item(row_index=2, metric_value=22.25),
        ]
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "defects = 11.5" in answer
        assert "defects = 22.25" in answer

    def test_z_score_included_when_present(self):
        evidence = [make_anomaly_evidence_item(z_score=5.08)]
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "(z-score 5.08)" in answer

    def test_z_score_omitted_when_missing(self):
        evidence = [make_anomaly_evidence_item(z_score=None)]
        finding = make_anomaly_finding_with_evidence(evidence)

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "(z-score" not in answer


@pytest.mark.unit
class TestContextualAnomalyDirectAnswer:
    def test_mean_comparison_appears_when_mean_exists(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    metric_name="defects",
                    metric_value=52.0,
                    mean=8.2,
                    z_score=5.08,
                    extra_context={"production_line": "Line 2"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert (
            "Line 2: defects = 52, compared with an average of 8.2 (z-score 5.08)."
            in answer
        )

    def test_mean_comparison_omitted_when_mean_absent(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    metric_name="attendance_rate",
                    metric_value=51.0,
                    z_score=-5.61,
                    extra_context={"school": "School C"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "compared with an average of" not in answer
        assert "School C: attendance_rate = 51 (z-score -5.61)" in answer

    def test_z_score_remains_visible_when_present_with_mean(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    metric_name="attendance_rate",
                    metric_value=51.0,
                    mean=88.3,
                    z_score=-5.61,
                    extra_context={"school": "School C"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "(z-score -5.61)" in answer

    def test_z_score_omitted_when_absent_with_mean(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    metric_name="attendance_rate",
                    metric_value=51.0,
                    mean=88.3,
                    z_score=None,
                    extra_context={"school": "School C"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert (
            "School C: attendance_rate = 51, compared with an average of 88.3."
            in answer
        )
        assert "(z-score" not in answer

    def test_context_label_from_single_non_metric_field(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    extra_context={"production_line": "Line 2"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Line 2: defects = 52" in answer
        assert "Row 126" not in answer

    def test_multiple_context_fields_combine_with_slash(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    extra_context={"school": "School C", "class": "5A"},
                )
            ]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "School C / 5A: defects = 52" in answer

    def test_row_fallback_when_no_context_fields(self):
        finding = make_anomaly_finding_with_evidence(
            [make_anomaly_evidence_item(row_index=126)]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Row 126: defects = 52" in answer

    def test_record_fallback_when_no_context_or_row_index(self):
        finding = make_anomaly_finding_with_evidence(
            [make_anomaly_evidence_item(row_index=None)]
        )

        answer = build_anomaly_direct_answer(finding)

        assert answer is not None
        assert "Record: defects = 52" in answer
        assert "Row " not in answer

    def test_adaptive_thresholds_unchanged_with_contextual_formatting(self):
        small = make_anomaly_finding_with_evidence(make_anomaly_evidence_items(5))
        medium = make_anomaly_finding_with_evidence(make_anomaly_evidence_items(6))
        large = make_anomaly_finding_with_evidence(make_anomaly_evidence_items(21))

        small_answer = build_anomaly_direct_answer(small)
        medium_answer = build_anomaly_direct_answer(medium)
        large_answer = build_anomaly_direct_answer(large)

        assert small_answer is not None
        assert medium_answer is not None
        assert large_answer is not None
        assert small_answer.count("- Row ") == 5
        assert "Affected records:" in small_answer
        assert medium_answer.count("- Row ") == 3
        assert "3 additional anomalous records were also identified." in medium_answer
        assert "- Row " not in large_answer
        assert (
            "See supporting evidence for the complete list of affected records."
            in large_answer
        )
