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
    return "generic"


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

    for index, item in enumerate(evidence, start=1):
        _render_evidence_item(item, index, evidence_type)
        if index < len(evidence):
            st.divider()


def _bucketed_findings(result: AnalysisResult) -> list[Finding]:
    return (
        result.report.high_priority_findings
        + result.report.medium_priority_findings
        + result.report.low_priority_findings
    )


def _render_finding(finding: Finding) -> None:
    badge = _severity_badge(finding.severity)
    st.markdown(f"{badge} · **{finding.title}**")
    st.markdown(finding.description)

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