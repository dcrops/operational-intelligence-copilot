"""
Regression tests for Milestone 5–6 behaviours.

Covers:
- schema-aware metric resolution
- question-aware dimension selection
- identifier exclusion
- trend volatility detection
- ambiguity clarification
- anomaly direction consistency
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.models import AnalysisRequest, ClarificationRequest
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.schema_resolution import (
    is_identifier_column,
    non_identifier_dimensions,
    resolve_dimension_from_question,
    resolve_metric_from_question,
)
from src.operational_intelligence.trend_analysis import TrendAnalysisTool, _classify_trend
from ui.analysis_service import run_analysis
from ui.anomaly_presentation import anomaly_business_description, anomaly_direction_label

MANUFACTURING_METRICS = ["defects", "downtime_minutes", "units_produced"]
MANUFACTURING_DIMENSIONS = [
    "production_line",
    "shift",
    "site",
    "supervisor",
]
WORKFORCE_METRICS = ["hours", "overtime_hours", "absence_days"]
WORKFORCE_DIMENSIONS = [
    "employee_id",
    "employee_name",
    "department",
    "location",
    "manager",
    "employment_type",
]


def _trend_metric_names(findings) -> set[str]:
    names: set[str] = set()
    for finding in findings:
        if "trend" not in finding.title.lower():
            continue
        for item in finding.evidence:
            if item.metric_name:
                names.add(item.metric_name)
    return names


def _anomaly_findings(findings):
    return [finding for finding in findings if "anomaly" in finding.title.lower()]


class TestSchemaAwareMetricResolution:
    def test_partial_metric_token_resolves_to_longest_match(self):
        question = "How has downtime changed over time?"
        assert resolve_metric_from_question(question, MANUFACTURING_METRICS) == "downtime_minutes"

    def test_pipeline_trend_uses_resolved_metric_not_first_profile_metric(
        self,
        manufacturing_df,
        manufacturing_profile,
        manufacturing_trend_request,
    ):
        assert manufacturing_profile.potential_metrics[0] == "defects"

        findings = OperationalPipeline().run(
            manufacturing_trend_request,
            manufacturing_df,
            [manufacturing_profile],
        )

        assert isinstance(findings, list)
        assert _trend_metric_names(findings) == {"downtime_minutes"}

    def test_generic_anomaly_question_does_not_resolve_single_metric(self):
        assert (
            resolve_metric_from_question("What looks unusual?", MANUFACTURING_METRICS)
            is None
        )


class TestQuestionAwareDimensionSelection:
    def test_manufacturing_variance_resolves_production_line_and_defects(self):
        question = "Which production line has the highest defects?"
        assert (
            resolve_dimension_from_question(question, MANUFACTURING_DIMENSIONS)
            == "production_line"
        )
        assert resolve_metric_from_question(question, MANUFACTURING_METRICS) == "defects"

    def test_workforce_variance_resolves_department_and_hours(self):
        question = "Which department has the highest hours?"
        assert resolve_dimension_from_question(question, WORKFORCE_DIMENSIONS) == "department"
        assert resolve_metric_from_question(question, WORKFORCE_METRICS) == "hours"

    def test_pipeline_variance_uses_question_resolved_dimension(
        self,
        workforce_df,
        workforce_profile,
        workforce_variance_request,
    ):
        findings = OperationalPipeline().run(
            workforce_variance_request,
            workforce_df,
            [workforce_profile],
        )

        assert isinstance(findings, list)
        variance_findings = [
            finding for finding in findings if "variance" in finding.title.lower()
        ]
        assert variance_findings
        assert any(
            item.supporting_context.get("department") is not None
            or "department" in str(item.supporting_context)
            for finding in variance_findings
            for item in finding.evidence
        )


class TestIdentifierExclusion:
    @pytest.mark.parametrize(
        ("column_name", "expected"),
        [
            ("employee_id", True),
            ("record_id", True),
            ("transaction_id", True),
            ("uuid", True),
            ("employee_number", True),
            ("department", False),
            ("production_line", False),
        ],
    )
    def test_is_identifier_column(self, column_name: str, expected: bool):
        assert is_identifier_column(column_name) is expected

    def test_non_identifier_dimensions_exclude_id_like_columns(self):
        filtered = non_identifier_dimensions(WORKFORCE_DIMENSIONS)
        assert "employee_id" not in filtered
        assert "department" in filtered

    def test_clarification_dimension_options_exclude_identifiers(
        self,
        workforce_profile,
    ):
        request = AnalysisRequest(
            question="Which group has the highest values?",
            dataset_names=["workforce_demo_v2"],
        )
        clarification = detect_clarification(
            request,
            ["variance_analysis"],
            workforce_profile,
        )

        assert isinstance(clarification, ClarificationRequest)
        assert "employee_id" not in clarification.options


class TestTrendVolatilityDetection:
    def test_classifier_detects_volatile_series(self):
        result = _classify_trend([100, 500, 100, 500, 100])
        assert result.trend_label == "volatile"

    def test_trend_tool_summary_mentions_volatile_for_alternating_series(self):
        dates = pd.date_range("2026-01-01", periods=5, freq="MS")
        df = pd.DataFrame({"month": dates, "hours": [100, 500, 100, 500, 100]})
        tool_result = TrendAnalysisTool().analyze(df, "month", "hours")

        assert tool_result.success is True
        assert tool_result.evidence_items[-1].supporting_context["trend_label"] == "volatile"
        assert "volatile" in tool_result.summary

    @pytest.mark.parametrize(
        ("values", "expected_label"),
        [
            ([100, 130, 160, 190, 220], "increasing"),
            ([220, 190, 160, 130, 100], "decreasing"),
            ([150, 152, 149, 151, 150], "stable"),
        ],
    )
    def test_classifier_directional_labels(self, values: list[float], expected_label: str):
        assert _classify_trend(values).trend_label == expected_label


class TestAmbiguityClarification:
    def test_ambiguous_trend_metric_returns_clarification(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        request = AnalysisRequest(
            question="How has performance changed over time?",
            dataset_names=["manufacturing_demo"],
        )
        outcome = OperationalPipeline().run(request, manufacturing_df, [manufacturing_profile])

        assert isinstance(outcome, ClarificationRequest)
        assert outcome.clarification_type == "metric"
        assert outcome.options == MANUFACTURING_METRICS

    def test_selected_metric_bypasses_repeat_clarification(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        request = AnalysisRequest(
            question="How has performance changed over time?",
            dataset_names=["manufacturing_demo"],
            selected_metrics=["downtime_minutes"],
        )
        outcome = OperationalPipeline().run(request, manufacturing_df, [manufacturing_profile])

        assert not isinstance(outcome, ClarificationRequest)
        assert _trend_metric_names(outcome) == {"downtime_minutes"}

    def test_multi_step_clarification_preserves_prior_metric_selection(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        question = "How has performance been affected?"

        metric_step = run_analysis(question, manufacturing_df, manufacturing_profile)
        assert metric_step.clarification is not None
        assert metric_step.clarification.clarification_type == "metric"

        dimension_step = run_analysis(
            question,
            manufacturing_df,
            manufacturing_profile,
            selected_metrics=["downtime_minutes"],
        )
        assert dimension_step.clarification is not None
        assert dimension_step.clarification.clarification_type == "dimension"
        assert dimension_step.request.selected_metrics == ["downtime_minutes"]

        completed = run_analysis(
            question,
            manufacturing_df,
            manufacturing_profile,
            selected_metrics=["downtime_minutes"],
            selected_dimensions=["production_line"],
        )
        assert completed.clarification is None
        assert completed.findings


class TestAnomalyDirectionConsistency:
    def test_all_high_anomaly_evidence_produces_high_presentation(self):
        from src.operational_intelligence.models import EvidenceItem, Finding

        evidence = [
            EvidenceItem(
                description=f"Anomaly row {index}",
                metric_name="units_produced",
                metric_value=900 + index,
                supporting_context={"anomaly_direction": "HIGH"},
            )
            for index in range(38)
        ]
        finding = Finding(
            title="Anomalies Detected by Anomaly Detection Tool",
            description="Anomalies were detected.",
            severity="HIGH",
            confidence="HIGH",
            evidence=evidence,
        )

        assert anomaly_direction_label(finding) == "high"
        assert "38 unusually high values" in anomaly_business_description(
            finding,
            "units produced",
        )

    def test_end_to_end_anomaly_direction_matches_direct_answer_and_business_copy(
        self,
        manufacturing_df,
        manufacturing_profile,
    ):
        result = run_analysis(
            "What looks unusual?",
            manufacturing_df,
            manufacturing_profile,
        )
        answer_generator = AnswerGenerator()

        units_produced_findings = [
            finding
            for finding in _anomaly_findings(result.findings)
            if finding.evidence
            and finding.evidence[0].metric_name == "units_produced"
        ]
        assert units_produced_findings

        finding = units_produced_findings[0]
        direct_answer = answer_generator._direct_anomaly_answer(finding)
        business_copy = anomaly_business_description(
            finding,
            finding.evidence[0].metric_name.replace("_", " "),
        )

        assert direct_answer is not None
        assert "HIGH" in direct_answer
        assert "high values" in business_copy
        assert "low values" not in business_copy
