from typing import List
from src.operational_intelligence.models import ToolResult, EvidenceItem, Finding

class RiskAssessmentTool:
    """
    Converts tool results and evidence into actionable operational findings.
    """

    def assess(
        self,
        tool_results: List[ToolResult]
    ) -> List[Finding]:
        """
        Assess a list of tool results and transform them into operational findings.

        Args:
            tool_results: List of ToolResult objects to assess.

        Returns:
            List[Finding]: Findings derived from tool results.
        """
        if not isinstance(tool_results, list) or not tool_results:
            raise ValueError("tool_results must be a non-empty list of ToolResult objects")

        findings: List[Finding] = []

        for tool_result in tool_results:
            # Failed tool result
            if not getattr(tool_result, "success", True):
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        confidence="HIGH",
                        title=f"Tool '{getattr(tool_result, 'tool_name', 'Unknown')}' failed to execute successfully",
                        description=getattr(tool_result, "summary", "No summary provided."),
                        evidence=[],
                        recommended_action=(
                            "Review data quality and tool configuration. "
                            "Address any issues before re-running the analysis."
                        )
                    )
                )
                continue

            # Skip successful results with no evidence
            evidence_items = getattr(tool_result, "evidence_items", []) or []
            if not evidence_items:
                continue

            tool_name = getattr(tool_result, "tool_name", "").lower()

            if tool_name == "anomaly_detection":
                findings.append(
                    Finding(
                        severity="HIGH",
                        confidence="HIGH",
                        title="Anomalies Detected by Anomaly Detection Tool",
                        description=getattr(tool_result, "summary", "Anomalies were detected."),
                        evidence=evidence_items,
                        recommended_action="Investigate the records identified as anomalous for potential operational issues."
                    )
                )
            elif tool_name == "variance_analysis":
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        confidence="MEDIUM",
                        title="Significant Variance Identified by Variance Analysis Tool",
                        description=getattr(tool_result, "summary", "Variance across groups detected."),
                        evidence=evidence_items,
                        recommended_action="Review discrepancies between highest and lowest categories to determine impact."
                    )
                )
            elif tool_name == "trend_analysis":
                findings.append(
                    Finding(
                        severity="LOW",
                        confidence="MEDIUM",
                        title="Trend Identified by Trend Analysis Tool",
                        description=getattr(tool_result, "summary", "Trend movement was observed."),
                        evidence=evidence_items,
                        recommended_action="Review the drivers for the observed trend to evaluate operational implications."
                    )
                )
            elif tool_name == "snapshot_analysis":
                findings.append(
                    Finding(
                        severity="LOW",
                        confidence="MEDIUM",
                        title="Snapshot Summary from Snapshot Analysis Tool",
                        description=getattr(tool_result, "summary", "Snapshot analysis completed."),
                        evidence=evidence_items,
                        recommended_action=(
                            "Review the scoped period value against the dataset baseline "
                            "to assess operational performance."
                        ),
                    )
                )
            # For other tool types with evidence, ignore per requirements

        return findings