"""Executive results content: Direct Answer, Executive Summary, Recommended Actions."""

from __future__ import annotations

import streamlit as st

from src.operational_intelligence.llm.narrative_governance import ADVISOR_SECTION_KEY_MESSAGE
from ui.components.results_shared import (
    humanise_report_text,
    render_section,
    should_render_recommended_actions,
)
from ui.models import AnalysisResult
from ui.narrative_presentation import (
    ASSESSMENT_CONFIDENCE_HEADING,
    EXECUTIVE_SUMMARY_HEADING,
    LIMITATIONS_HEADING,
    NARRATIVE_DISABLED_MESSAGE,
    format_assessment_confidence_level,
    format_executive_assessment_banner,
)


def render_direct_answer(result: AnalysisResult) -> None:
    def body() -> None:
        st.markdown(humanise_report_text(result, result.direct_answer))

    render_section("Direct Answer", body)


def render_executive_summary_content(result: AnalysisResult) -> None:
    """Render executive narrative content without audit verification blocks."""

    def body() -> None:
        narrative = result.narrative
        if narrative is None:
            st.info(NARRATIVE_DISABLED_MESSAGE)
            return

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

    render_section(EXECUTIVE_SUMMARY_HEADING, body)


def render_recommended_actions(result: AnalysisResult) -> None:
    if not should_render_recommended_actions(result.report):
        return

    def body() -> None:
        for step in result.report.recommended_next_steps:
            st.markdown(f"- {humanise_report_text(result, step)}")

    render_section("Recommended Actions", body)
