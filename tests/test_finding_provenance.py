"""Tests for Finding provenance fields (Milestone 9 Phase 9a)."""

from __future__ import annotations

import pytest

from src.operational_intelligence.models import EvidenceItem, Finding, ToolResult
from src.operational_intelligence.risk_assessment import RiskAssessmentTool
from src.operational_intelligence.investigation_suggestions import InvestigationSuggestionGenerator


pytestmark = pytest.mark.unit


class TestFindingModelProvenance:
    def test_finding_without_provenance_fields_remains_valid(self):
        finding = Finding(
            title="Legacy Finding",
            description="Created without provenance metadata.",
            severity="LOW",
            confidence="MEDIUM",
            evidence=[],
        )

        assert finding.finding_id is None
        assert finding.finding_type is None
        assert finding.source_tool is None

    def test_finding_accepts_valid_provenance_fields(self):
        finding = Finding(
            finding_id="finding-0",
            finding_type="anomaly",
            source_tool="anomaly_detection",
            title="Anomalies Detected by Anomaly Detection Tool",
            description="Anomalies were detected.",
            severity="HIGH",
            confidence="HIGH",
            evidence=[],
        )

        assert finding.finding_id == "finding-0"
        assert finding.finding_type == "anomaly"
        assert finding.source_tool == "anomaly_detection"

    def test_finding_type_rejects_invalid_values(self):
        with pytest.raises(ValueError, match="finding_type must be one of"):
            Finding(
                finding_type="unknown",
                title="Invalid",
                description="Invalid finding type.",
                severity="LOW",
                confidence="LOW",
            )

    def test_finding_type_is_normalized_to_lowercase(self):
        finding = Finding(
            finding_type="VARIANCE",
            title="Variance",
            description="Variance finding.",
            severity="MEDIUM",
            confidence="MEDIUM",
        )

        assert finding.finding_type == "variance"


class TestRiskAssessmentProvenance:
    @pytest.fixture
    def multi_tool_results(self) -> list[ToolResult]:
        return [
            ToolResult(
                tool_name="anomaly_detection",
                success=True,
                summary="1 anomalous value detected.",
                evidence_items=[
                    EvidenceItem(
                        description="Spike",
                        metric_name="hours",
                        metric_value=900.0,
                        supporting_context={"anomaly_direction": "HIGH"},
                    )
                ],
            ),
            ToolResult(
                tool_name="variance_analysis",
                success=True,
                summary="Variance detected across departments.",
                evidence_items=[
                    EvidenceItem(
                        description="Department comparison",
                        metric_name="hours",
                        metric_value=600.0,
                        supporting_context={
                            "department": "Ops",
                            "aggregation": "sum",
                            "comparison_direction": "top",
                            "is_comparison_target": True,
                        },
                    )
                ],
            ),
            ToolResult(
                tool_name="trend_analysis",
                success=True,
                summary="Trend increased over time.",
                evidence_items=[
                    EvidenceItem(
                        description="Period value",
                        metric_name="hours",
                        metric_value=200.0,
                        supporting_context={"aggregation": "sum"},
                    )
                ],
            ),
            ToolResult(
                tool_name="snapshot_analysis",
                success=True,
                summary="Snapshot completed.",
                evidence_items=[
                    EvidenceItem(
                        description="Snapshot value for April 2026.",
                        metric_name="attendance_rate",
                        metric_value=88.23,
                        supporting_context={
                            "analysis_mode": "snapshot",
                            "period_label": "April 2026",
                        },
                    )
                ],
            ),
        ]

    def test_assess_populates_finding_type_and_source_tool(self, multi_tool_results):
        findings = RiskAssessmentTool().assess(multi_tool_results)

        assert [(finding.finding_type, finding.source_tool) for finding in findings] == [
            ("anomaly", "anomaly_detection"),
            ("variance", "variance_analysis"),
            ("trend", "trend_analysis"),
            ("snapshot", "snapshot_analysis"),
        ]

    def test_assess_assigns_unique_finding_ids(self, multi_tool_results):
        findings = RiskAssessmentTool().assess(multi_tool_results)

        finding_ids = [finding.finding_id for finding in findings]
        assert finding_ids == ["finding-0", "finding-1", "finding-2", "finding-3"]
        assert len(set(finding_ids)) == len(finding_ids)

    def test_failed_tool_finding_uses_failure_type_and_source_tool(self):
        findings = RiskAssessmentTool().assess(
            [
                ToolResult(
                    tool_name="trend_analysis",
                    success=False,
                    summary="Trend analysis failed: missing date column.",
                    evidence_items=[],
                )
            ]
        )

        assert len(findings) == 1
        assert findings[0].finding_id == "finding-0"
        assert findings[0].finding_type == "failure"
        assert findings[0].source_tool == "trend_analysis"
        assert findings[0].severity == "MEDIUM"

    def test_existing_severity_and_title_behaviour_unchanged(self, multi_tool_results):
        findings = RiskAssessmentTool().assess(multi_tool_results)

        assert findings[0].severity == "HIGH"
        assert "Anomalies Detected" in findings[0].title
        assert findings[1].severity == "MEDIUM"
        assert "Variance" in findings[1].title
        assert findings[2].severity == "LOW"
        assert "Trend" in findings[2].title
        assert findings[3].severity == "LOW"
        assert "Snapshot Summary" in findings[3].title


class TestBackwardCompatibilityWithTitleFallbacks:
    def test_investigation_suggestions_still_work_without_provenance(self):
        finding = Finding(
            title="Trend Identified by Trend Analysis Tool",
            description="The total hours increased over time.",
            severity="LOW",
            confidence="MEDIUM",
            evidence=[
                EvidenceItem(
                    description="Period value",
                    metric_name="hours",
                    metric_value=100.0,
                    supporting_context={"aggregation": "sum", "trend_label": "increasing"},
                )
            ],
        )

        suggestions = InvestigationSuggestionGenerator().generate_for_finding(finding)

        assert suggestions

    def test_investigation_suggestions_still_work_with_provenance(self):
        finding = Finding(
            finding_id="finding-0",
            finding_type="trend",
            source_tool="trend_analysis",
            title="Trend Identified by Trend Analysis Tool",
            description="The total hours increased over time.",
            severity="LOW",
            confidence="MEDIUM",
            evidence=[
                EvidenceItem(
                    description="Period value",
                    metric_name="hours",
                    metric_value=100.0,
                    supporting_context={"aggregation": "sum", "trend_label": "increasing"},
                )
            ],
        )

        suggestions = InvestigationSuggestionGenerator().generate_for_finding(finding)

        assert suggestions
