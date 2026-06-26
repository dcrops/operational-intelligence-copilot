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
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
    split_follow_up_investigations,
)
from ui.models import AnalysisResult
from ui.results_headings import SECTION_OVERVIEW
from ui.results_presentation import (
    ZONE_INVESTIGATION,
    close_section_heading,
    format_investigation_overview_bullets,
    open_section_heading,
    render_level2_heading,
    render_overview_bullets,
)


def render_overview_content(result: AnalysisResult) -> None:
    """Render Analysis Overview beneath the Overview section heading."""

    def body() -> None:
        bullets = format_investigation_overview_bullets(result)
        render_overview_bullets(bullets)

    render_section(ANALYSIS_OVERVIEW_HEADING, body, zone=ZONE_INVESTIGATION)


def render_investigation_sections(result: AnalysisResult) -> None:
    """Render investigation sections without the outer Investigation group heading."""

    def render_analytical_findings() -> None:
        findings = bucketed_findings(result)

        if not findings:
            st.caption("No findings were identified from the analysis.")
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
            st.caption("No follow-up investigations suggested.")

    render_level2_heading("Suggested Follow-Up Investigations", zone=ZONE_INVESTIGATION)
    with st.container(border=True):
        render_investigations()
    st.markdown("")


def render_investigation_bundle(result: AnalysisResult) -> None:
    """Render Overview and Investigation content inside a disclosure group."""
    open_section_heading(zone=ZONE_INVESTIGATION, tier=1)
    st.markdown(f"#### {SECTION_OVERVIEW}")
    close_section_heading()
    render_overview_content(result)
    render_investigation_sections(result)
