import pytest

from src.operational_intelligence.models import AnalysisRequest, EvidenceItem, ToolResult
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.risk_assessment import RiskAssessmentTool
from tests.support.factories import manufacturing_bundle
from ui.analysis_service import run_analysis


@pytest.mark.unit
class TestRiskAssessmentTool:
    def test_assess_maps_tool_results_to_severity_findings_with_actions(self):
        tool_results = [
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
        ]

        findings = RiskAssessmentTool().assess(tool_results)

        assert len(findings) == 3
        assert findings[0].severity == "HIGH"
        assert findings[0].recommended_action
        assert "Anomalies Detected" in findings[0].title
        assert findings[1].severity == "MEDIUM"
        assert "Variance" in findings[1].title
        assert findings[2].severity == "LOW"
        assert "Trend" in findings[2].title
        assert all(finding.recommended_action for finding in findings)

    def test_assess_records_failed_tool_as_medium_finding(self):
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
        assert findings[0].severity == "MEDIUM"
        assert "failed to execute successfully" in findings[0].title
        assert "Review data quality" in findings[0].recommended_action

    def test_assess_rejects_empty_tool_results(self):
        with pytest.raises(ValueError, match="tool_results must be a non-empty list"):
            RiskAssessmentTool().assess([])


@pytest.mark.integration
class TestRiskAssessmentPipelineSmoke:
    def test_risk_intent_question_routes_risk_and_produces_actionable_findings(self):
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects and what is the risk?",
            df,
            profile,
        )

        assert "risk_assessment" in result.routes
        assert "variance_analysis" in result.routes
        assert result.findings
        assert all(finding.severity in {"HIGH", "MEDIUM", "LOW", "INFO"} for finding in result.findings)
        assert any(finding.recommended_action for finding in result.findings)
        assert any(
            "Variance" in finding.title or "variance" in finding.title.lower()
            for finding in result.findings
        )

    def test_pipeline_findings_pass_through_risk_assessment_layer(self):
        df, profile = manufacturing_bundle()
        findings = OperationalPipeline().run(
            AnalysisRequest(
                question="Which production line has the highest defects?",
                dataset_names=[profile.dataset_name],
            ),
            df,
            [profile],
        )

        assert isinstance(findings, list)
        assert len(findings) == 1
        assert findings[0].severity == "MEDIUM"
        assert findings[0].recommended_action == (
            "Review discrepancies between highest and lowest categories to determine impact."
        )
