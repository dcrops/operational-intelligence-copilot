from src.operational_intelligence.anomaly_direct_answer import build_anomaly_direct_answer
from src.operational_intelligence.models import AnalysisRequest, ExecutiveReport, Finding
from src.operational_intelligence.question_semantics import (
    CAUSATION_DISCLAIMER,
    CAUSATION_FINDINGS_INTRO,
    causation_requested,
)


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

        lines.append("\nSuggested Follow-Up Investigations:")
        if report.suggested_follow_up_investigations:
            for suggestion in report.suggested_follow_up_investigations:
                lines.append(f"- {suggestion}")
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
                analytical_answer = overview
            else:
                analytical_answer = self._resolve_analytical_direct_answer(request, findings)
        else:
            analytical_answer = self._resolve_analytical_direct_answer(request, findings)

        if causation_requested(request.question):
            return self._apply_causation_disclaimer(analytical_answer, findings)

        return analytical_answer

    def _resolve_analytical_direct_answer(
        self,
        request: AnalysisRequest,
        findings: list[Finding],
    ) -> str:
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

    def _apply_causation_disclaimer(
        self,
        analytical_answer: str,
        findings: list[Finding],
    ) -> str:
        parts = [CAUSATION_DISCLAIMER]
        if findings:
            parts.append(CAUSATION_FINDINGS_INTRO)
            parts.append(analytical_answer)
        return "\n\n".join(parts)

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

        targets = [
            item
            for item in finding.evidence
            if isinstance(item.metric_value, (int, float))
            and item.supporting_context.get("is_comparison_target") is True
        ]
        if not targets:
            targets = [
                item for item in finding.evidence
                if isinstance(item.metric_value, (int, float))
            ]
        if not targets:
            return None

        direction = targets[0].supporting_context.get("comparison_direction", "top")
        aggregation = targets[0].supporting_context.get("aggregation", "sum")
        agg_label = "mean" if aggregation == "mean" else "total"
        metric_name = targets[0].metric_name or "metric"

        if direction == "dual" and len(targets) >= 1:
            top_item = next(
                (
                    item
                    for item in targets
                    if item.supporting_context.get("comparison_extreme") == "top"
                ),
                max(targets, key=lambda item: item.metric_value),
            )
            bottom_item = next(
                (
                    item
                    for item in targets
                    if item.supporting_context.get("comparison_extreme") == "bottom"
                ),
                min(targets, key=lambda item: item.metric_value),
            )
            top_label = self._extract_dimension_label(top_item.supporting_context)
            bottom_label = self._extract_dimension_label(bottom_item.supporting_context)
            if top_label and bottom_label:
                return (
                    f"{top_label} recorded the highest {agg_label} {metric_name} "
                    f"({top_item.metric_value:g}), and {bottom_label} recorded the "
                    f"lowest {agg_label} {metric_name} ({bottom_item.metric_value:g})."
                )

        item = targets[0]
        dimension_label = self._extract_dimension_label(item.supporting_context)
        direction_word = "highest" if direction == "top" else "lowest"

        if dimension_label:
            return (
                f"The {dimension_label} recorded the {direction_word} {agg_label} "
                f"{metric_name} ({item.metric_value:g})."
            )

        return (
            f"The {direction_word} {agg_label} {metric_name} was {item.metric_value:g}."
        )

    def _direct_anomaly_answer(self, finding: Finding) -> str | None:
        return build_anomaly_direct_answer(finding)

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
            "aggregation",
            "comparison_direction",
            "comparison_extreme",
            "is_comparison_target",
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