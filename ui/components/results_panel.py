from datetime import datetime

import streamlit as st

from src.operational_intelligence.models import EvidenceItem, Finding
from ui.models import AnalysisResult


SEVERITY_BADGES = {
    "HIGH": "🔴 **HIGH**",
    "MEDIUM": "🟠 **MEDIUM**",
    "LOW": "🟡 **LOW**",
    "INFO": "🔵 **INFO**",
}

MAX_EVIDENCE_DISPLAY = 5


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


def _metric_label(finding: Finding, default: str = "hours") -> str:
    for item in finding.evidence:
        if item.metric_name:
            return item.metric_name.replace("_", " ")
    return default


def _anomaly_business_description(finding: Finding) -> str:
    count = len(finding.evidence)
    metric = _metric_label(finding)
    high_count = sum(
        1
        for item in finding.evidence
        if str(item.supporting_context.get("anomaly_direction", "")).upper() == "HIGH"
    )
    low_count = count - high_count

    if count == 0:
        return (
            "Unusual workforce values were identified that differ significantly "
            "from normal workforce patterns."
        )

    if high_count >= low_count:
        direction = "high"
    else:
        direction = "low"

    value_label = "value" if count == 1 else "values"
    return (
        f"{count} unusually {direction} {metric} {value_label} were identified "
        f"that differ significantly from normal workforce patterns."
    )


def _variance_business_description(finding: Finding) -> str:
    if not finding.evidence:
        return (
            "Significant differences were observed across workforce groups "
            "that may warrant operational review."
        )

    metric = _metric_label(finding)
    numeric_evidence = [
        item
        for item in finding.evidence
        if isinstance(item.metric_value, int | float)
    ]
    if not numeric_evidence:
        return (
            "Significant differences were observed across workforce groups "
            "that may warrant operational review."
        )

    highest = max(numeric_evidence, key=lambda item: item.metric_value)
    lowest = min(numeric_evidence, key=lambda item: item.metric_value)
    dimension_name, highest_group = _context_dimension(highest.supporting_context)
    _, lowest_group = _context_dimension(lowest.supporting_context)
    group_label = dimension_name or "group"

    if highest_group and lowest_group:
        return (
            f"Significant differences were observed between {group_label}s, "
            f"with {highest_group} recording substantially higher {metric} "
            f"than {lowest_group}."
        )

    return (
        f"Significant differences were observed in {metric} across workforce "
        f"{group_label}s."
    )


def _trend_business_description(finding: Finding) -> str:
    metric = _metric_label(finding).capitalize()
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
        st.markdown(f"- **Metric name:** {item.metric_name or '—'}")
        st.markdown(f"- **Metric value:** {_format_number(item.metric_value)}")
        return

    if evidence_type == "trend":
        date_name, date_value = _context_dimension(ctx)
        if date_name and date_value:
            st.markdown(f"- **Date ({date_name}):** {date_value}")
        else:
            st.markdown("- **Date / month:** —")
        st.markdown(f"- **Metric name:** {item.metric_name or '—'}")
        st.markdown(f"- **Metric value:** {_format_number(item.metric_value)}")
        return

    if item.metric_name:
        st.markdown(f"- **Metric name:** {item.metric_name}")
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


def render_results(result: AnalysisResult) -> None:
    st.subheader("Results")

    st.markdown("#### Direct Answer")
    with st.container(border=True):
        st.markdown(result.direct_answer)

    st.markdown("#### Executive Summary")
    with st.container(border=True):
        st.markdown(result.report.executive_summary)

    st.markdown("#### Findings")
    with st.container(border=True):
        findings = _bucketed_findings(result)

        if not findings:
            st.caption("No findings were identified from the analysis.")
        else:
            for index, finding in enumerate(findings, start=1):
                _render_finding(finding)
                if index < len(findings):
                    st.divider()

    st.markdown("#### Recommended Actions")
    with st.container(border=True):
        if result.report.recommended_next_steps:
            for step in result.report.recommended_next_steps:
                st.markdown(f"- {step}")
        else:
            st.caption("No recommended actions.")

    st.markdown("#### System Transparency")
    with st.container(border=True):
        st.markdown(f"**Question:** {result.request.question}")
        st.markdown(f"**Routed tools:** {', '.join(result.routes) or 'None'}")
        st.markdown(f"**Findings returned:** {len(result.findings)}")

    st.markdown("#### LLM Explanation")
    with st.container(border=True):
        st.info(
            "LLM explanations are not enabled yet. "
            "The deterministic analysis above is the primary answer."
        )