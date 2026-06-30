"""Investigation results content: findings, reasoning, and follow-up investigations."""

from __future__ import annotations

import streamlit as st

from ui.components.results_shared import (
    bucketed_findings,
    humanise_report_text,
    render_executive_reasoning,
    render_finding,
    render_section,
)
from ui.executive_reasoning_presentation import (
    ANALYTICAL_FINDINGS_HEADING,
    split_follow_up_investigations,
)
from ui.models import AnalysisResult
from ui.results_presentation import (
    ZONE_INVESTIGATION,
    render_empty_state,
    render_level2_heading,
)


def render_investigation_sections(result: AnalysisResult) -> None:
    """Render investigation sections without the outer Investigation group heading."""
    st.markdown('<div class="oic-findings-body">', unsafe_allow_html=True)

    def render_analytical_findings() -> None:
        findings = bucketed_findings(result)

        if not findings:
            render_empty_state(
                "No findings were identified from the analysis.",
                title="No findings",
            )
        else:
            for index, finding in enumerate(findings, start=1):
                render_finding(finding)
                if index < len(findings):
                    st.divider()

    render_section(ANALYTICAL_FINDINGS_HEADING, render_analytical_findings, zone=ZONE_INVESTIGATION)

    render_executive_reasoning(result.report)

    def render_investigations() -> None:
        investigations = result.report.suggested_follow_up_investigations
        if investigations:
            humanised = [
                humanise_report_text(result, suggestion) for suggestion in investigations
            ]
            presentation = split_follow_up_investigations(humanised)
            for suggestion in presentation.visible:
                st.markdown(f"- {suggestion}")
            if presentation.additional:
                with st.expander(presentation.expander_label, expanded=False):
                    for suggestion in presentation.additional:
                        st.markdown(f"- {suggestion}")
        else:
            render_empty_state(
                "No follow-up investigations were suggested for this analysis.",
                title="No follow-ups",
            )

    render_level2_heading("Suggested Follow-Up Investigations", zone=ZONE_INVESTIGATION)
    st.markdown('<div class="oic-follow-up-block">', unsafe_allow_html=True)
    with st.container(border=True):
        render_investigations()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("")


def render_findings_bundle(result: AnalysisResult) -> None:
    """Render analytical findings content for the Findings tab."""
    render_investigation_sections(result)


def render_investigation_bundle(result: AnalysisResult) -> None:
    """Deprecated alias for disclosure-era callers; use render_findings_bundle."""
    render_findings_bundle(result)
