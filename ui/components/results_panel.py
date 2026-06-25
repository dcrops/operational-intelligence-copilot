from datetime import datetime

import streamlit as st

from src.operational_intelligence.llm.narrative_governance import ADVISOR_SECTION_KEY_MESSAGE
from src.operational_intelligence.models import EvidenceItem, ExecutiveReport, Finding
from ui.anomaly_presentation import anomaly_business_description
from ui.executive_reasoning_presentation import (
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
    EXECUTIVE_REASONING_HEADING,
    format_analysis_overview,
    format_executive_conclusion,
    format_operational_assessment,
    format_priority_action,
    should_show_executive_conclusions,
    should_show_executive_reasoning,
    should_show_operational_assessment,
    should_show_priority_actions,
    should_show_recommended_actions,
    split_follow_up_investigations,
)
from ui.metric_presentation import humanise_metric_name, humanise_metric_references_in_text
from ui.models import AnalysisResult
from ui.narrative_presentation import (
    ASSESSMENT_CONFIDENCE_HEADING,
    EXECUTIVE_NARRATIVE_AI_ASSISTED_HEADING,
    GOVERNANCE_CAPTION,
    LIMITATIONS_HEADING,
    NARRATIVE_DISABLED_MESSAGE,
    TECHNICAL_DETAILS_HEADING,
    format_assessment_confidence_level,
    format_executive_assessment_banner,
    format_generation_details,
)
from ui.transparency import (
    format_auto_resolved_trail,
    format_clarification_trail,
    format_metrics_analysed_trail,
    format_snapshot_contributors_trail,
    format_snapshot_trail,
    format_temporal_filter_trail,
)
from ui.variance_presentation import variance_business_description


SEVERITY_BADGES = {
    "HIGH": "🔴 **HIGH**",
    "MEDIUM": "🟠 **MEDIUM**",
    "LOW": "🟡 **LOW**",
    "INFO": "🔵 **INFO**",
}

MAX_EVIDENCE_DISPLAY = 5


def _render_section(title: str, render_body, *, bordered: bool = True) -> None:
    st.markdown(f"#### {title}")
    if bordered:
        with st.container(border=True):
            render_body()
    else:
        render_body()
    st.markdown("")


def _severity_badge(severity: str) -> str:
    return SEVERITY_BADGES.get(severity.upper(), f"**{severity}**")


def _format_context_value(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    text = str(value)

    if text.endswith(" 00:00:00"):
        return text[:-9]

    return text


def _evidence_type(finding: Finding) -> str:
    title = finding.title.lower()
    if "anomaly" in title:
        return "anomaly"
    if "variance" in title:
        return "variance"
    if "trend" in title:
        return "trend"
    if "failed" in title or "tool '" in title:
        return "failure"
    return "generic"


def _metric_label(finding: Finding, default: str = "metric") -> str:
    for item in finding.evidence:
        if item.metric_name:
            return humanise_metric_name(item.metric_name)
    return default


def _anomaly_business_description(finding: Finding) -> str:
    metric = _metric_label(finding)
    return anomaly_business_description(finding, metric)


def _variance_business_description(finding: Finding) -> str:
    metric = _metric_label(finding)
    return variance_business_description(finding, metric)


def _trend_business_description(finding: Finding) -> str:
    metric = _metric_label(finding)
    description = finding.description.lower()

    if "volatile" in description:
        return (
            f"{metric} fluctuated significantly over the reporting period, "
            "with repeated ups and downs and no consistent directional movement."
        )
    if "increas" in description:
        movement = "increased steadily"
        trend = "upward"
    elif "decreas" in description:
        movement = "decreased steadily"
        trend = "downward"
    elif "stable" in description:
        movement = "remained relatively stable"
        trend = "stable"
    else:
        movement = "changed over time"
        trend = "emerging"

    return (
        f"{metric} {movement} over the reporting period, "
        f"indicating a sustained {trend} trend."
    )


def _failure_business_description(finding: Finding) -> str:
    return (
        "One analysis step could not be completed successfully. "
        "Review the dataset quality and configuration before re-running the analysis."
    )


def _business_friendly_description(finding: Finding) -> str:
    """Translate technical finding descriptions into operational language for the UI."""
    mapping = {
        "anomaly": _anomaly_business_description,
        "variance": _variance_business_description,
        "trend": _trend_business_description,
        "failure": _failure_business_description,
    }
    presenter = mapping.get(_evidence_type(finding))
    if presenter is not None:
        return presenter(finding)
    return finding.description


def _context_dimension(ctx: dict) -> tuple[str | None, str | None]:
    ignored = {
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

    for key, value in ctx.items():
        if key not in ignored and value is not None:
            return key, _format_context_value(value)

    return None, None


def _format_number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _render_evidence_summary(item: EvidenceItem, evidence_type: str) -> None:
    ctx = item.supporting_context

    if evidence_type == "anomaly":
        st.markdown(f"- **Row index:** {ctx.get('row_index', '—')}")
        st.markdown(f"- **Observed value:** {_format_number(item.metric_value)}")
        st.markdown(f"- **Mean:** {_format_number(ctx.get('mean', '—'))}")
        st.markdown(
            f"- **Standard deviation:** {_format_number(ctx.get('standard_deviation', '—'))}"
        )
        st.markdown(f"- **Z-score:** {_format_number(ctx.get('z_score', '—'))}")
        st.markdown(f"- **Direction:** {ctx.get('anomaly_direction', '—')}")
        return

    if evidence_type == "variance":
        dimension_name, dimension_value = _context_dimension(ctx)
        if dimension_name and dimension_value:
            st.markdown(f"- **Dimension ({dimension_name}):** {dimension_value}")
        else:
            st.markdown("- **Dimension value:** —")
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
        st.markdown(f"- **Metric value:** {_format_number(item.metric_value)}")
        return

    if evidence_type == "trend":
        date_name, date_value = _context_dimension(ctx)
        if date_name and date_value:
            st.markdown(f"- **Date ({date_name}):** {date_value}")
        else:
            st.markdown("- **Date / month:** —")
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
        st.markdown(f"- **Metric value:** {_format_number(item.metric_value)}")
        return

    if item.metric_name:
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
    if item.metric_value is not None:
        st.markdown(f"- **Metric value:** {_format_number(item.metric_value)}")
    if item.dataset_name:
        st.markdown(f"- **Dataset:** {item.dataset_name}")


def _render_evidence_item(item: EvidenceItem, index: int, evidence_type: str) -> None:
    st.markdown(f"**Evidence {index}:** {item.description}")
    _render_evidence_summary(item, evidence_type)

    if item.supporting_context:
        with st.expander("Raw evidence", expanded=False):
            st.json(item.supporting_context)


def _render_evidence(evidence: list[EvidenceItem], finding: Finding) -> None:
    if not evidence:
        st.caption("No evidence attached.")
        return

    evidence_type = _evidence_type(finding)
    total_count = len(evidence)
    visible_evidence = evidence[:MAX_EVIDENCE_DISPLAY]

    for index, item in enumerate(visible_evidence, start=1):
        _render_evidence_item(item, index, evidence_type)
        if index < len(visible_evidence):
            st.divider()

    if total_count > MAX_EVIDENCE_DISPLAY:
        st.caption(
            f"Showing top {MAX_EVIDENCE_DISPLAY} of {total_count} evidence items."
        )


def _collect_metric_names(result: AnalysisResult) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    for finding in result.findings:
        for item in finding.evidence:
            if item.metric_name and item.metric_name not in seen:
                names.append(item.metric_name)
                seen.add(item.metric_name)

    for metric in result.metrics_analysed or []:
        if metric not in seen:
            names.append(metric)
            seen.add(metric)

    for theme in result.report.executive_themes:
        if theme.theme_label and theme.theme_label not in seen:
            names.append(theme.theme_label)
            seen.add(theme.theme_label)

    return names


def _humanise_report_text(result: AnalysisResult, text: str) -> str:
    return humanise_metric_references_in_text(text, _collect_metric_names(result))


def _bucketed_findings(result: AnalysisResult) -> list[Finding]:
    return (
        result.report.high_priority_findings
        + result.report.medium_priority_findings
        + result.report.low_priority_findings
    )


def _render_finding(finding: Finding) -> None:
    badge = _severity_badge(finding.severity)
    st.markdown(f"{badge} · **{finding.title}**")
    st.markdown(_business_friendly_description(finding))

    if finding.recommended_action:
        st.caption(f"Suggested action: {finding.recommended_action}")

    with st.expander(f"Evidence ({len(finding.evidence)})", expanded=False):
        _render_evidence(finding.evidence, finding)


def _render_operational_assessment(report: ExecutiveReport) -> None:
    assessment = report.operational_assessment
    if assessment is None:
        return

    presentation = format_operational_assessment(assessment)
    st.markdown(f"### {presentation.level_display}")
    st.markdown(presentation.explanation)


def _render_executive_conclusions(report: ExecutiveReport) -> None:
    if not report.executive_conclusions:
        return

    for index, conclusion in enumerate(report.executive_conclusions):
        presentation = format_executive_conclusion(conclusion, report)
        st.markdown(f"##### {presentation.title}")
        st.markdown(f"### {presentation.insight}")
        st.markdown(f"**{presentation.evidence_heading}**")
        for summary in presentation.evidence_bullets:
            st.caption(f"• {summary}")
        if index < len(report.executive_conclusions) - 1:
            st.markdown("")


def _render_priority_actions(report: ExecutiveReport) -> None:
    if not report.priority_actions:
        return

    for index, action in enumerate(report.priority_actions):
        presentation = format_priority_action(action)
        st.markdown(f"**{presentation.header}**")
        st.markdown(f"### {presentation.action_text}")
        st.markdown(f"**{presentation.reason_label}**")
        st.caption(presentation.reason_text)
        if index < len(report.priority_actions) - 1:
            st.markdown("")


def _render_executive_reasoning(report: ExecutiveReport) -> None:
    if not should_show_executive_reasoning(report):
        return

    st.markdown(f"#### {EXECUTIVE_REASONING_HEADING}")

    if should_show_operational_assessment(report):
        st.markdown("##### Operational Assessment")
        _render_operational_assessment(report)

    if should_show_executive_conclusions(report):
        if should_show_operational_assessment(report):
            st.markdown("")
        st.markdown("##### Executive Conclusions")
        _render_executive_conclusions(report)

    if should_show_priority_actions(report):
        if should_show_operational_assessment(report) or should_show_executive_conclusions(
            report
        ):
            st.markdown("")
        st.markdown("##### Priority Actions")
        _render_priority_actions(report)

    st.markdown("")


def _render_recommended_actions(result: AnalysisResult) -> None:
    if not should_show_recommended_actions(result.report):
        return

    def body() -> None:
        for step in result.report.recommended_next_steps:
            st.markdown(f"- {_humanise_report_text(result, step)}")

    _render_section("Recommended Actions", body)


def render_results(result: AnalysisResult) -> None:
    st.subheader("Results")

    def render_direct_answer() -> None:
        st.markdown(_humanise_report_text(result, result.direct_answer))

    _render_section("Direct Answer", render_direct_answer)

    def render_analysis_overview() -> None:
        overview = format_analysis_overview(
            findings=result.findings,
            routes=result.routes,
            report=result.report,
        )
        for bullet in overview.bullets:
            st.markdown(f"- {bullet}")

    _render_section(ANALYSIS_OVERVIEW_HEADING, render_analysis_overview)

    def render_analytical_findings() -> None:
        findings = _bucketed_findings(result)

        if not findings:
            st.caption("No findings were identified from the analysis.")
        else:
            for index, finding in enumerate(findings, start=1):
                _render_finding(finding)
                if index < len(findings):
                    st.divider()

    _render_section(ANALYTICAL_FINDINGS_HEADING, render_analytical_findings)

    _render_executive_reasoning(result.report)

    _render_recommended_actions(result)

    def render_investigations() -> None:
        investigations = result.report.suggested_follow_up_investigations
        if investigations:
            humanised = [
                _humanise_report_text(result, suggestion) for suggestion in investigations
            ]
            presentation = split_follow_up_investigations(humanised)
            for suggestion in presentation.visible:
                st.markdown(f"- {suggestion}")
            if presentation.additional:
                with st.expander(presentation.expander_label, expanded=False):
                    for suggestion in presentation.additional:
                        st.markdown(f"- {suggestion}")
        else:
            st.caption("No follow-up investigations suggested.")

    _render_section("Suggested Follow-Up Investigations", render_investigations)

    def render_transparency() -> None:
        st.markdown(f"**Question:** {result.request.question}")
        st.markdown(f"**Routed tools:** {', '.join(result.routes) or 'None'}")
        st.markdown(f"**Findings returned:** {len(result.findings)}")

        temporal_filter_lines = format_temporal_filter_trail(result.temporal_filter)
        if temporal_filter_lines:
            st.markdown("**Applied temporal filter:**")
            for line in temporal_filter_lines:
                st.markdown(f"- {line}")

        snapshot_lines = format_snapshot_trail(result.snapshot_context)
        if snapshot_lines:
            st.markdown("**Snapshot mode activated:**")
            for line in snapshot_lines:
                st.markdown(f"- {line}")

        contributor_lines = format_snapshot_contributors_trail(result.findings)
        if contributor_lines:
            st.markdown("**Snapshot contributors:**")
            for line in contributor_lines:
                st.markdown(f"- {line}")

        clarifications = format_clarification_trail(result.request)
        st.markdown("**Clarifications:**")
        if clarifications:
            for line in clarifications:
                st.markdown(f"- {line}")
        else:
            st.markdown("None required")

        auto_resolved = format_auto_resolved_trail(
            result.request,
            result.findings,
            result.routes,
            metrics_analysed=result.metrics_analysed or [],
        )
        st.markdown("**Automatically resolved:**")
        if auto_resolved:
            for line in auto_resolved:
                st.markdown(f"- {line}")
        else:
            st.markdown("None")

        metrics_analysed = format_metrics_analysed_trail(result.metrics_analysed)
        if metrics_analysed:
            st.markdown("**Metrics analysed:**")
            for metric in metrics_analysed:
                st.markdown(f"- {metric}")

    _render_section("System Transparency", render_transparency)

    _render_ai_assisted_narrative(result)


def _render_ai_assisted_narrative(result: AnalysisResult) -> None:
    def body() -> None:
        narrative = result.narrative
        if narrative is None:
            st.info(NARRATIVE_DISABLED_MESSAGE)
            return

        st.caption(GOVERNANCE_CAPTION)

        if narrative.executive_assessment is not None:
            st.markdown(
                format_executive_assessment_banner(narrative.executive_assessment),
                unsafe_allow_html=True,
            )

        for section in narrative.sections:
            st.markdown(f"##### {section.title}")
            st.markdown(section.content)

            if (
                section.title == ADVISOR_SECTION_KEY_MESSAGE
                and narrative.assessment_confidence is not None
            ):
                confidence = narrative.assessment_confidence
                st.markdown(f"##### {ASSESSMENT_CONFIDENCE_HEADING}")
                st.markdown(format_assessment_confidence_level(confidence))
                st.markdown(confidence.rationale)

        st.markdown(f"##### {LIMITATIONS_HEADING}")
        st.markdown(narrative.limitations)

        generation_details = format_generation_details(narrative)
        if generation_details:
            with st.expander(TECHNICAL_DETAILS_HEADING):
                for line in generation_details:
                    st.caption(f"- {line}")

    _render_section(EXECUTIVE_NARRATIVE_AI_ASSISTED_HEADING, body)