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
from ui.results_headings import FOLLOW_UP_ASK_BUTTON_LABEL
from ui.results_presentation import (
    ZONE_INVESTIGATION,
    render_empty_state,
    render_level2_heading,
)
from ui.state import apply_suggested_question


def _render_follow_up_suggestion(display_text: str, question_text: str, *, key: str) -> None:
    text_column, button_column = st.columns([8, 1.2], vertical_alignment="center")
    with text_column:
        st.markdown(f"- {display_text}")
    with button_column:
        if st.button(FOLLOW_UP_ASK_BUTTON_LABEL, key=key):
            apply_suggested_question(question_text)


def _render_follow_up_suggestions(
    result: AnalysisResult,
    suggestions: list[str],
    *,
    key_prefix: str,
) -> None:
    for index, suggestion in enumerate(suggestions):
        display_text = humanise_report_text(result, suggestion)
        _render_follow_up_suggestion(
            display_text,
            display_text,
            key=f"{key_prefix}_{index}",
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
                render_finding(finding, report=result.report)
                if index < len(findings):
                    st.divider()

    render_section(ANALYTICAL_FINDINGS_HEADING, render_analytical_findings, zone=ZONE_INVESTIGATION)

    render_executive_reasoning(result.report)

    def render_investigations() -> None:
        investigations = result.report.suggested_follow_up_investigations
        if investigations:
            presentation = split_follow_up_investigations(investigations)
            visible = presentation.visible
            if visible:
                _render_follow_up_suggestions(result, visible, key_prefix="follow_up_visible")
                if presentation.additional:
                    with st.expander(presentation.expander_label, expanded=False):
                        _render_follow_up_suggestions(
                            result,
                            presentation.additional,
                            key_prefix="follow_up_additional",
                        )
            else:
                render_empty_state(
                    "Follow-up investigations are covered by the Priority Actions above.",
                    title="No additional follow-ups",
                )
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
