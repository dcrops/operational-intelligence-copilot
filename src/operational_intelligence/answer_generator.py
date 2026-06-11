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
        lines.append(self._build_direct_answer(request, findings, report))

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

    def _build_direct_answer(
        self,
        request: AnalysisRequest,
        findings: list[Finding],
        report: ExecutiveReport,
    ) -> str:
        if self._is_broad_analysis_question(request.question):
            overview = self._build_executive_overview(report)
            if overview:
                return overview

        severity_order = ["HIGH", "MEDIUM", "LOW", "INFO"]
        grouped = {severity: [] for severity in severity_order}

        for finding in findings:
            severity = (finding.severity or "INFO").upper()
            if severity not in grouped:
                severity = "INFO"
            grouped[severity].append(finding)

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

    def _is_broad_analysis_question(self, question: str) -> bool:
        q = question.strip().lower()
        broad_phrases = [
            "analyse this dataset",
            "analyze this dataset",
            "analyse the dataset",
            "analyze the dataset",
            "review this dataset",
            "review the dataset",
            "assess this dataset",
            "assess the dataset",
            "summarise this dataset",
            "summarize this dataset",
            "give me an overview",
            "what should i know",
        ]
        return any(phrase in q for phrase in broad_phrases)

    def _build_executive_overview(self, report: ExecutiveReport) -> str:
        messages: list[str] = []

        if report.high_priority_findings:
            messages.append("a high-priority anomaly or issue requiring investigation")

        if report.medium_priority_findings:
            messages.append("a medium-priority variance or comparison finding")

        if report.low_priority_findings:
            messages.append("a lower-priority trend or contextual finding")

        if not messages:
            return "No priority findings were identified from the analysis."

        if len(messages) == 1:
            finding_summary = messages[0]
        elif len(messages) == 2:
            finding_summary = f"{messages[0]} and {messages[1]}"
        else:
            finding_summary = f"{', '.join(messages[:-1])}, and {messages[-1]}"

        return (
            "Operational analysis identified multiple areas requiring attention, "
            f"including {finding_summary}."
        )

    def _direct_variance_answer(self, finding: Finding) -> str | None:
        if not finding.evidence:
            return None

        evidence_with_values = [
            item for item in finding.evidence
            if isinstance(item.metric_value, (int, float))
        ]

        if not evidence_with_values:
            return None

        highest = max(evidence_with_values, key=lambda item: item.metric_value)
        dimension_label = self._extract_dimension_label(highest.supporting_context)

        if dimension_label:
            return (
                f"The {dimension_label} recorded the highest total "
                f"{highest.metric_name} ({highest.metric_value:g})."
            )

        return f"The highest total {highest.metric_name} was {highest.metric_value:g}."

    def _direct_anomaly_answer(self, finding: Finding) -> str | None:
        if not finding.evidence:
            return None

        evidence_count = len(finding.evidence)
        metric_name = finding.evidence[0].metric_name or "metric"

        if evidence_count == 1:
            item = finding.evidence[0]
            value = item.metric_value
            if value is None:
                return None

            direction = item.supporting_context.get("anomaly_direction")
            if direction:
                return (
                    f"An unusual {direction} value was detected for "
                    f"{metric_name}: {value:g}."
                )

            return f"An unusual value was detected for {metric_name}: {value:g}."

        numeric_items = [
            item for item in finding.evidence
            if isinstance(item.metric_value, (int, float))
        ]
        if not numeric_items:
            return None

        extreme_item = max(numeric_items, key=lambda item: item.metric_value)
        extreme_value = extreme_item.metric_value
        metric_name = extreme_item.metric_name or metric_name
        direction = extreme_item.supporting_context.get("anomaly_direction")

        if direction:
            return (
                f"{evidence_count} unusual {direction} values were detected for "
                f"{metric_name}. The most extreme value was {extreme_value:g}."
            )

        return (
            f"{evidence_count} unusual values were detected for {metric_name}. "
            f"The most extreme value was {extreme_value:g}."
        )

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