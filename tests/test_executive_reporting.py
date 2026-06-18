import pytest

from src.operational_intelligence.executive_reasoning import ExecutiveReasoningEngine
from src.operational_intelligence.models import Finding
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from tests.support.builders import make_sample_findings


@pytest.mark.unit
class TestExecutiveReportGenerator:
    def test_buckets_findings_by_severity(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)

        assert len(report.high_priority_findings) == 1
        assert report.high_priority_findings[0].severity == "HIGH"
        assert len(report.medium_priority_findings) == 1
        assert report.medium_priority_findings[0].severity == "MEDIUM"
        assert len(report.low_priority_findings) == 1
        assert report.low_priority_findings[0].severity == "LOW"

    def test_executive_summary_contains_correct_counts(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)

        assert report.executive_summary == (
            "Operational analysis identified 3 finding(s): "
            "1 high priority, 1 medium priority, and 1 low priority."
        )

    def test_recommended_next_steps_preserve_unique_actions_in_order(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)

        assert report.recommended_next_steps == [
            "Investigate the records identified as anomalous for potential operational issues.",
            "Review discrepancies between highest and lowest categories to determine impact.",
            "Review the drivers for the observed trend to evaluate operational implications.",
        ]

    def test_empty_findings_produce_zero_count_summary(self):
        report = ExecutiveReportGenerator().generate([])

        assert report.executive_summary == (
            "Operational analysis identified 0 finding(s): "
            "0 high priority, 0 medium priority, and 0 low priority."
        )
        assert report.high_priority_findings == []
        assert report.medium_priority_findings == []
        assert report.low_priority_findings == []
        assert report.recommended_next_steps == []

    def test_info_findings_are_bucketed_as_low_priority(self):
        finding = Finding(
            title="Informational Finding",
            description="Context only.",
            severity="INFO",
            confidence="LOW",
            evidence=[],
            recommended_action="Monitor the metric periodically.",
        )
        report = ExecutiveReportGenerator().generate([finding])

        assert report.low_priority_findings == [finding]
        assert report.high_priority_findings == []
        assert report.recommended_next_steps == ["Monitor the metric periodically."]


    def test_suggested_follow_up_investigations_populated_for_sample_findings(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)

        assert report.suggested_follow_up_investigations
        assert len(report.suggested_follow_up_investigations) >= 3

    def test_empty_findings_have_empty_suggested_investigations(self):
        report = ExecutiveReportGenerator().generate([])

        assert report.suggested_follow_up_investigations == []

    def test_recommended_next_steps_remain_separate_from_investigations(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)

        assert report.recommended_next_steps
        assert report.suggested_follow_up_investigations
        assert set(report.recommended_next_steps).isdisjoint(
            set(report.suggested_follow_up_investigations)
        )

    def test_rejects_non_list_input(self):
        with pytest.raises(ValueError, match="findings must be a list"):
            ExecutiveReportGenerator().generate("not a list")  # type: ignore[arg-type]

    def test_accepts_reasoning_result_and_populates_report_fields(self):
        findings = make_sample_findings()
        reasoning = ExecutiveReasoningEngine().reason(findings)

        report = ExecutiveReportGenerator().generate(findings, reasoning=reasoning)

        assert report.executive_themes == reasoning.themes
        assert report.operational_assessment == reasoning.operational_assessment
        assert report.executive_conclusions == reasoning.conclusions
        assert report.priority_actions == reasoning.priority_actions

    def test_reasoning_preserves_legacy_severity_buckets_and_summary(self):
        findings = make_sample_findings()
        reasoning = ExecutiveReasoningEngine().reason(findings)

        legacy_report = ExecutiveReportGenerator().generate(findings)
        integrated_report = ExecutiveReportGenerator().generate(findings, reasoning=reasoning)

        assert integrated_report.executive_summary == legacy_report.executive_summary
        assert integrated_report.high_priority_findings == legacy_report.high_priority_findings
        assert integrated_report.medium_priority_findings == legacy_report.medium_priority_findings
        assert integrated_report.low_priority_findings == legacy_report.low_priority_findings
        assert (
            integrated_report.suggested_follow_up_investigations
            == legacy_report.suggested_follow_up_investigations
        )

    def test_reasoning_recommended_next_steps_mirror_priority_actions(self):
        findings = make_sample_findings()
        reasoning = ExecutiveReasoningEngine().reason(findings)

        report = ExecutiveReportGenerator().generate(findings, reasoning=reasoning)

        assert reasoning.priority_actions
        assert report.recommended_next_steps == [
            action.action for action in reasoning.priority_actions
        ]

    def test_without_reasoning_falls_back_to_finding_recommended_actions(self):
        findings = make_sample_findings()

        report = ExecutiveReportGenerator().generate(findings)

        assert report.recommended_next_steps == [
            "Investigate the records identified as anomalous for potential operational issues.",
            "Review discrepancies between highest and lowest categories to determine impact.",
            "Review the drivers for the observed trend to evaluate operational implications.",
        ]
        assert report.operational_assessment is None
        assert report.executive_conclusions == []
        assert report.priority_actions == []
        assert report.executive_themes == []
