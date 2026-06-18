from typing import List

from src.operational_intelligence.models import EvidenceItem, Finding, ToolResult


class RiskAssessmentTool:
    """
    Converts tool results and evidence into actionable operational findings.
    """

    _TOOL_FINDING_TYPE = {
        "anomaly_detection": "anomaly",
        "variance_analysis": "variance",
        "trend_analysis": "trend",
        "snapshot_analysis": "snapshot",
    }

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
        finding_index = 0

        for tool_result in tool_results:
            tool_name = getattr(tool_result, "tool_name", "Unknown")
            normalized_tool_name = str(tool_name).strip().lower()

            if not getattr(tool_result, "success", True):
                findings.append(
                    self._build_finding(
                        finding_index=finding_index,
                        finding_type="failure",
                        source_tool=normalized_tool_name or "pipeline",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title=f"Tool '{tool_name}' failed to execute successfully",
                        description=getattr(tool_result, "summary", "No summary provided."),
                        evidence=[],
                        recommended_action=(
                            "Review data quality and tool configuration. "
                            "Address any issues before re-running the analysis."
                        ),
                    )
                )
                finding_index += 1
                continue

            evidence_items = getattr(tool_result, "evidence_items", []) or []
            if not evidence_items:
                continue

            finding_type = self._TOOL_FINDING_TYPE.get(normalized_tool_name)
            if finding_type is None:
                continue

            findings.append(
                self._build_finding_for_tool(
                    finding_index=finding_index,
                    tool_name=normalized_tool_name,
                    finding_type=finding_type,
                    tool_result=tool_result,
                    evidence_items=evidence_items,
                )
            )
            finding_index += 1

        return findings

    @staticmethod
    def _build_finding(
        *,
        finding_index: int,
        finding_type: str,
        source_tool: str,
        severity: str,
        confidence: str,
        title: str,
        description: str,
        evidence: list[EvidenceItem],
        recommended_action: str | None,
    ) -> Finding:
        return Finding(
            finding_id=f"finding-{finding_index}",
            finding_type=finding_type,
            source_tool=source_tool,
            severity=severity,
            confidence=confidence,
            title=title,
            description=description,
            evidence=evidence,
            recommended_action=recommended_action,
        )

    def _build_finding_for_tool(
        self,
        *,
        finding_index: int,
        tool_name: str,
        finding_type: str,
        tool_result: ToolResult,
        evidence_items: list[EvidenceItem],
    ) -> Finding:
        if finding_type == "anomaly":
            return self._build_finding(
                finding_index=finding_index,
                finding_type=finding_type,
                source_tool=tool_name,
                severity="HIGH",
                confidence="HIGH",
                title="Anomalies Detected by Anomaly Detection Tool",
                description=getattr(tool_result, "summary", "Anomalies were detected."),
                evidence=evidence_items,
                recommended_action=(
                    "Investigate the records identified as anomalous for potential operational issues."
                ),
            )

        if finding_type == "variance":
            return self._build_finding(
                finding_index=finding_index,
                finding_type=finding_type,
                source_tool=tool_name,
                severity="MEDIUM",
                confidence="MEDIUM",
                title="Significant Variance Identified by Variance Analysis Tool",
                description=getattr(tool_result, "summary", "Variance across groups detected."),
                evidence=evidence_items,
                recommended_action=(
                    "Review discrepancies between highest and lowest categories to determine impact."
                ),
            )

        if finding_type == "trend":
            return self._build_finding(
                finding_index=finding_index,
                finding_type=finding_type,
                source_tool=tool_name,
                severity="LOW",
                confidence="MEDIUM",
                title="Trend Identified by Trend Analysis Tool",
                description=getattr(tool_result, "summary", "Trend movement was observed."),
                evidence=evidence_items,
                recommended_action=(
                    "Review the drivers for the observed trend to evaluate operational implications."
                ),
            )

        return self._build_finding(
            finding_index=finding_index,
            finding_type=finding_type,
            source_tool=tool_name,
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
