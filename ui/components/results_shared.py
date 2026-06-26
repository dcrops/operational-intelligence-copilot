"""Shared rendering helpers for results presentation sections."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.operational_intelligence.models import EvidenceItem, ExecutiveReport, Finding
from ui.anomaly_presentation import anomaly_business_description
from ui.executive_reasoning_presentation import (
    format_executive_conclusion,
    format_operational_assessment,
    format_priority_action,
    should_show_executive_conclusions,
    should_show_executive_reasoning,
    should_show_operational_assessment,
    should_show_priority_actions,
    should_show_recommended_actions,
)
from ui.metric_presentation import humanise_metric_name, humanise_metric_references_in_text
from ui.models import AnalysisResult
from ui.variance_presentation import variance_business_description

SEVERITY_BADGES = {
    "HIGH": "🔴 **HIGH**",
    "MEDIUM": "🟠 **MEDIUM**",
    "LOW": "🟡 **LOW**",
    "INFO": "🔵 **INFO**",
}

MAX_EVIDENCE_DISPLAY = 5


def render_section(title: str, render_body, *, bordered: bool = True) -> None:
    st.markdown(f"#### {title}")
    if bordered:
        with st.container(border=True):
            render_body()
    else:
        render_body()
    st.markdown("")


def severity_badge(severity: str) -> str:
    return SEVERITY_BADGES.get(severity.upper(), f"**{severity}**")


def format_context_value(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    text = str(value)

    if text.endswith(" 00:00:00"):
        return text[:-9]

    return text


def evidence_type(finding: Finding) -> str:
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


def metric_label(finding: Finding, default: str = "metric") -> str:
    for item in finding.evidence:
        if item.metric_name:
            return humanise_metric_name(item.metric_name)
    return default


def anomaly_business_description_for(finding: Finding) -> str:
    return anomaly_business_description(finding, metric_label(finding))


def variance_business_description_for(finding: Finding) -> str:
    return variance_business_description(finding, metric_label(finding))


def trend_business_description_for(finding: Finding) -> str:
    metric = metric_label(finding)
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


def failure_business_description_for(finding: Finding) -> str:
    return (
        "One analysis step could not be completed successfully. "
        "Review the dataset quality and configuration before re-running the analysis."
    )


def business_friendly_description(finding: Finding) -> str:
    mapping = {
        "anomaly": anomaly_business_description_for,
        "variance": variance_business_description_for,
        "trend": trend_business_description_for,
        "failure": failure_business_description_for,
    }
    presenter = mapping.get(evidence_type(finding))
    if presenter is not None:
        return presenter(finding)
    return finding.description


def context_dimension(ctx: dict) -> tuple[str | None, str | None]:
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
            return key, format_context_value(value)

    return None, None


def format_number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def render_evidence_summary(item: EvidenceItem, evidence_type_name: str) -> None:
    ctx = item.supporting_context

    if evidence_type_name == "anomaly":
        st.markdown(f"- **Row index:** {ctx.get('row_index', '—')}")
        st.markdown(f"- **Observed value:** {format_number(item.metric_value)}")
        st.markdown(f"- **Mean:** {format_number(ctx.get('mean', '—'))}")
        st.markdown(
            f"- **Standard deviation:** {format_number(ctx.get('standard_deviation', '—'))}"
        )
        st.markdown(f"- **Z-score:** {format_number(ctx.get('z_score', '—'))}")
        st.markdown(f"- **Direction:** {ctx.get('anomaly_direction', '—')}")
        return

    if evidence_type_name == "variance":
        dimension_name, dimension_value = context_dimension(ctx)
        if dimension_name and dimension_value:
            st.markdown(f"- **Dimension ({dimension_name}):** {dimension_value}")
        else:
            st.markdown("- **Dimension value:** —")
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
        st.markdown(f"- **Metric value:** {format_number(item.metric_value)}")
        return

    if evidence_type_name == "trend":
        date_name, date_value = context_dimension(ctx)
        if date_name and date_value:
            st.markdown(f"- **Date ({date_name}):** {date_value}")
        else:
            st.markdown("- **Date / month:** —")
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
        st.markdown(f"- **Metric value:** {format_number(item.metric_value)}")
        return

    if item.metric_name:
        st.markdown(f"- **Metric name:** {humanise_metric_name(item.metric_name)}")
    if item.metric_value is not None:
        st.markdown(f"- **Metric value:** {format_number(item.metric_value)}")
    if item.dataset_name:
        st.markdown(f"- **Dataset:** {item.dataset_name}")


def render_evidence_item(item: EvidenceItem, index: int, evidence_type_name: str) -> None:
    st.markdown(f"**Evidence {index}:** {item.description}")
    render_evidence_summary(item, evidence_type_name)

    if item.supporting_context:
        with st.expander("Raw evidence", expanded=False):
            st.json(item.supporting_context)


def render_evidence(evidence: list[EvidenceItem], finding: Finding) -> None:
    if not evidence:
        st.caption("No evidence attached.")
        return

    evidence_type_name = evidence_type(finding)
    total_count = len(evidence)
    visible_evidence = evidence[:MAX_EVIDENCE_DISPLAY]

    for index, item in enumerate(visible_evidence, start=1):
        render_evidence_item(item, index, evidence_type_name)
        if index < len(visible_evidence):
            st.divider()

    if total_count > MAX_EVIDENCE_DISPLAY:
        st.caption(
            f"Showing top {MAX_EVIDENCE_DISPLAY} of {total_count} evidence items."
        )


def collect_metric_names(result: AnalysisResult) -> list[str]:
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


def humanise_report_text(result: AnalysisResult, text: str) -> str:
    return humanise_metric_references_in_text(text, collect_metric_names(result))


def bucketed_findings(result: AnalysisResult) -> list[Finding]:
    return (
        result.report.high_priority_findings
        + result.report.medium_priority_findings
        + result.report.low_priority_findings
    )


def render_finding(finding: Finding) -> None:
    badge = severity_badge(finding.severity)
    st.markdown(f"{badge} · **{finding.title}**")
    st.markdown(business_friendly_description(finding))

    if finding.recommended_action:
        st.caption(f"Suggested action: {finding.recommended_action}")

    with st.expander(f"Evidence ({len(finding.evidence)})", expanded=False):
        render_evidence(finding.evidence, finding)


def render_operational_assessment(report: ExecutiveReport) -> None:
    assessment = report.operational_assessment
    if assessment is None:
        return

    presentation = format_operational_assessment(assessment)
    st.markdown(f"### {presentation.level_display}")
    st.markdown(presentation.explanation)


def render_executive_conclusions(report: ExecutiveReport) -> None:
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


def render_priority_actions(report: ExecutiveReport) -> None:
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


def render_executive_reasoning(report: ExecutiveReport) -> None:
    from ui.executive_reasoning_presentation import EXECUTIVE_REASONING_HEADING

    if not should_show_executive_reasoning(report):
        return

    st.markdown(f"#### {EXECUTIVE_REASONING_HEADING}")

    if should_show_operational_assessment(report):
        st.markdown("##### Operational Assessment")
        render_operational_assessment(report)

    if should_show_executive_conclusions(report):
        if should_show_operational_assessment(report):
            st.markdown("")
        st.markdown("##### Executive Conclusions")
        render_executive_conclusions(report)

    if should_show_priority_actions(report):
        if should_show_operational_assessment(report) or should_show_executive_conclusions(
            report
        ):
            st.markdown("")
        st.markdown("##### Priority Actions")
        render_priority_actions(report)

    st.markdown("")


def should_render_recommended_actions(report: ExecutiveReport) -> bool:
    return should_show_recommended_actions(report)
