import pytest

from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest, EvidenceItem, Finding
from src.operational_intelligence.question_semantics import (
    CAUSATION_DISCLAIMER,
    CAUSATION_FINDINGS_INTRO,
)
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from tests.support.assertions import assert_answer_contains_standard_sections
from tests.support.builders import (
    make_anomaly_evidence_item,
    make_anomaly_finding_with_evidence,
    make_sample_findings,
    make_variance_evidence_item,
    make_variance_finding,
)


def _request(question: str = "Which department has the highest hours?") -> AnalysisRequest:
    return AnalysisRequest(
        question=question,
        dataset_names=["workforce_synthetic"],
    )


@pytest.mark.unit
class TestAnswerGeneratorFullOutput:
    def test_generated_answer_contains_all_standard_sections(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)
        answer = AnswerGenerator().generate(_request(), findings, report)

        assert_answer_contains_standard_sections(answer)
        assert "[HIGH] Anomalies Detected by Anomaly Detection Tool" in answer
        assert "[MEDIUM] Significant Variance Identified by Variance Analysis Tool" in answer
        assert "[LOW] Trend Identified by Trend Analysis Tool" in answer
        assert "- Investigate the records identified as anomalous" in answer

    def test_generated_answer_includes_suggested_follow_up_investigations(self):
        findings = make_sample_findings()
        report = ExecutiveReportGenerator().generate(findings)
        answer = AnswerGenerator().generate(_request(), findings, report)

        assert "Suggested Follow-Up Investigations:" in answer
        assert "Show unusual" in answer


    def test_no_findings_path_returns_expected_message(self):
        report = ExecutiveReportGenerator().generate([])
        answer = AnswerGenerator().generate(_request(), [], report)

        assert answer == "No findings were identified from the analysis."
        assert "Direct Answer:" not in answer


@pytest.mark.unit
class TestAnswerGeneratorDirectAnswers:
    def test_direct_anomaly_answer_aligns_with_evidence_direction(self):
        finding = make_anomaly_finding_with_evidence(
            [
                make_anomaly_evidence_item(
                    metric_name="overtime_hours",
                    metric_value=100.0,
                    row_index=42,
                    z_score=8.5,
                    anomaly_direction="HIGH",
                )
            ]
        )
        answer = AnswerGenerator()._direct_anomaly_answer(finding)

        assert answer is not None
        assert "1 unusual HIGH value was detected for overtime_hours." in answer
        assert "Affected records:" in answer
        assert "Row 42" in answer
        assert "overtime_hours = 100" in answer
        assert "(z-score 8.50)" in answer

    def test_direct_variance_answer_respects_top_direction_and_sum_aggregation(self):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="production_line",
                    dimension_value="Line B",
                    metric_name="defects",
                    metric_value=32.0,
                    aggregation="sum",
                    comparison_direction="top",
                )
            ]
        )
        answer = AnswerGenerator()._direct_variance_answer(finding)

        assert answer is not None
        assert "highest total defects" in answer
        assert "Line B" in answer
        assert "32" in answer

    def test_direct_variance_answer_respects_bottom_direction_and_mean_aggregation(self):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School B",
                    metric_name="attendance_rate",
                    metric_value=71.0,
                    aggregation="mean",
                    comparison_direction="bottom",
                )
            ]
        )
        answer = AnswerGenerator()._direct_variance_answer(finding)

        assert answer is not None
        assert "lowest mean attendance_rate" in answer
        assert "School B" in answer

    def test_direct_variance_answer_supports_dual_comparison(self):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="department",
                    dimension_value="Ops",
                    metric_name="hours",
                    metric_value=600.0,
                    aggregation="sum",
                    comparison_direction="dual",
                    comparison_extreme="top",
                ),
                make_variance_evidence_item(
                    dimension_key="department",
                    dimension_value="HR",
                    metric_name="hours",
                    metric_value=480.0,
                    aggregation="sum",
                    comparison_direction="dual",
                    comparison_extreme="bottom",
                ),
            ]
        )
        answer = AnswerGenerator()._direct_variance_answer(finding)

        assert answer is not None
        assert "highest total hours" in answer
        assert "lowest total hours" in answer
        assert "Ops" in answer
        assert "HR" in answer

    def test_direct_trend_answer_uses_finding_description_with_volatile_wording(self):
        finding = Finding(
            title="Trend Identified by Trend Analysis Tool",
            description=(
                "The total hours increased from 100 to 220 (120.0% change). "
                "The series was volatile over the period."
            ),
            severity="LOW",
            confidence="MEDIUM",
            evidence=[],
        )
        report = ExecutiveReportGenerator().generate([finding])
        direct = AnswerGenerator()._build_direct_answer(
            _request("How has hours changed over time?"),
            [finding],
            report,
        )

        assert "volatile" in direct.lower()
        assert "120.0% change" in direct


@pytest.mark.unit
class TestCausationAnswerHandling:
    def test_causal_question_prefixes_direct_answer_with_disclaimer(self):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School B",
                    metric_name="attendance_rate",
                    metric_value=71.0,
                    aggregation="mean",
                    comparison_direction="bottom",
                )
            ]
        )
        report = ExecutiveReportGenerator().generate([finding])
        direct = AnswerGenerator()._build_direct_answer(
            _request("What caused attendance to drop?"),
            [finding],
            report,
        )

        assert direct.startswith(CAUSATION_DISCLAIMER)
        assert CAUSATION_FINDINGS_INTRO in direct
        assert "lowest mean attendance_rate" in direct

    def test_non_causal_question_omits_causation_disclaimer(self):
        finding = make_variance_finding(
            [
                make_variance_evidence_item(
                    dimension_key="school",
                    dimension_value="School B",
                    metric_name="attendance_rate",
                    metric_value=71.0,
                    aggregation="mean",
                    comparison_direction="bottom",
                )
            ]
        )
        report = ExecutiveReportGenerator().generate([finding])
        direct = AnswerGenerator()._build_direct_answer(
            _request("Which school has the lowest attendance?"),
            [finding],
            report,
        )

        assert CAUSATION_DISCLAIMER not in direct
        assert "lowest mean attendance_rate" in direct
