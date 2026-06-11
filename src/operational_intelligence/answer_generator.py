from src.operational_intelligence.models import AnalysisRequest, ExecutiveReport, Finding


class AnswerGenerator:
    """
    Generates a user-facing answer from findings and an executive report.
    """

    def generate(
        self,
        request: AnalysisRequest,
        findings: list[Finding],
        report: ExecutiveReport,
    ) -> str:
        """
        Format a direct answer plus report-style supporting sections.
        """
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an AnalysisRequest")
        if not isinstance(findings, list):
            raise ValueError("findings must be a list")
        if not isinstance(report, ExecutiveReport):
            raise ValueError("report must be an ExecutiveReport")

        if not findings:
            return "No findings were identified from the analysis."

        lines: list[str] = []

        lines.append("Direct Answer:")
        lines.append(self._build_direct_answer(findings))

        lines.append("\nExecutive Summary:")
        lines.append(report.executive_summary.strip())

        self._format_findings(lines, "High Priority Findings", report.high_priority_findings)
        self._format_findings(lines, "Medium Priority Findings", report.medium_priority_findings)
        self._format_findings(lines, "Low Priority Findings", report.low_priority_findings)

        lines.append("\nRecommended Next Steps:")
        if report.recommended_next_steps:
            for step in report.recommended_next_steps:
                lines.append(f"- {step}")
        else:
            lines.append("  None.")

        return "\n".join(lines)

    def _build_direct_answer(self, findings: list[Finding]) -> str:
        # Define severity order: HIGH, MEDIUM, LOW, INFO
        severity_order = ['HIGH', 'MEDIUM', 'LOW', 'INFO']

        # Group findings by severity while preserving their original order in each group
        grouped = {severity: [] for severity in severity_order}
        for finding in findings:
            severity = (getattr(finding, "severity", "INFO") or "INFO").upper()
            if severity not in grouped:
                severity = "INFO"
            grouped[severity].append(finding)

        # Iterate by ordered severity levels
        for severity in severity_order:
            for finding in grouped[severity]:
                title = finding.title.lower()

                if "variance" in title:
                    answer = self._direct_variance_answer(finding)
                    if answer:
                        return answer

                if "anomaly" in title:
                    answer = self._direct_anomaly_answer(finding)
                    if answer:
                        return answer

                if "trend" in title and finding.description:
                    return finding.description.strip()

        return "A direct answer could not be determined from the available findings."

    def _direct_variance_answer(self, finding: Finding) -> str | None:
        if not finding.evidence:
            return None

        evidence_with_values = [
            item for item in finding.evidence
            if isinstance(item.metric_value, int | float)
        ]

        if not evidence_with_values:
            return None

        highest = max(evidence_with_values, key=lambda item: item.metric_value)

        dimension_label = self._extract_dimension_label(highest.supporting_context)

        if dimension_label:
            return (
                f"{dimension_label} had the highest "
                f"{highest.metric_name} value at {highest.metric_value}."
            )

        return (
            f"The highest {highest.metric_name} value was "
            f"{highest.metric_value}."
        )

    def _direct_anomaly_answer(self, finding: Finding) -> str | None:
        if not finding.evidence:
            return None

        item = finding.evidence[0]
        direction = item.supporting_context.get("anomaly_direction")
        metric_name = item.metric_name or "metric"
        value = item.metric_value

        if value is None:
            return None

        if direction:
            return (
                f"An unusual {direction} value was detected for "
                f"{metric_name}: {value}."
            )

        return f"An unusual value was detected for {metric_name}: {value}."

    def _extract_dimension_label(
        self,
        supporting_context: dict[str, str | int | float | bool | None],
    ) -> str | None:
        ignored_keys = {
            "row_index",
            "mean",
            "standard_deviation",
            "z_score",
            "anomaly_direction",
        }

        for key, value in supporting_context.items():
            if key not in ignored_keys and value is not None:
                return f"{key} '{value}'"

        return None

    def _format_findings(
        self,
        lines: list[str],
        title: str,
        items: list[Finding],
    ) -> None:
        lines.append(f"\n{title}:")
        if items:
            for finding in items:
                entry = f"- [{finding.severity}] {finding.title}"
                if finding.description:
                    entry += f": {finding.description}"
                lines.append(entry)
        else:
            lines.append("  None.")