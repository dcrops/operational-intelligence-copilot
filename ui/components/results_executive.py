"""Executive results content: Direct Answer, Executive Summary, Recommended Actions."""

from __future__ import annotations

import streamlit as st

from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_EXECUTIVE_ACTIONS,
    ADVISOR_SECTION_KEY_MESSAGE,
    ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
    ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
    ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
    ADVISOR_SECTION_WHY_THIS_MATTERS,
)
from src.operational_intelligence.llm.narrative_models import NarrativeSection
from ui.components.results_shared import (
    humanise_report_text,
    render_section,
    should_render_recommended_actions,
)
from ui.executive_reasoning_presentation import DEFAULT_INVESTIGATION_LIMIT
from ui.models import AnalysisResult
from ui.narrative_presentation import (
    ASSESSMENT_CONFIDENCE_HEADING,
    EXECUTIVE_SUMMARY_HEADING,
    LIMITATIONS_HEADING,
    NARRATIVE_DISABLED_MESSAGE,
    format_assessment_confidence_level,
    format_executive_assessment_banner,
)
from ui.results_headings import (
    ASSESSMENT_CONFIDENCE_DETAILS_LABEL,
    MORE_EXECUTIVE_ACTIONS_LABEL,
    MORE_RECOMMENDATIONS_LABEL,
)
from ui.results_presentation import (
    ZONE_EXECUTIVE,
    render_hero_body,
    render_level2_heading,
    render_numbered_items,
    split_action_lines,
)

_COLLAPSED_SUMMARY_SECTIONS = frozenset(
    {
        ADVISOR_SECTION_WHY_THIS_MATTERS,
        ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
        ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
        ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
    }
)


def render_direct_answer(result: AnalysisResult) -> None:
    def body() -> None:
        render_hero_body(humanise_report_text(result, result.direct_answer))

    render_section("Direct Answer", body, variant="hero", zone=ZONE_EXECUTIVE, bordered=False)


def _render_capped_numbered_actions(
    content: str,
    *,
    more_label: str,
    limit: int = DEFAULT_INVESTIGATION_LIMIT,
) -> None:
    visible_lines, additional_lines = split_action_lines(content, limit=limit)
    if visible_lines:
        render_numbered_items(visible_lines)

    if additional_lines:
        with st.expander(more_label, expanded=False):
            render_numbered_items(additional_lines)


def _render_executive_actions_section(section: NarrativeSection) -> None:
    render_level2_heading(section.title, zone=ZONE_EXECUTIVE)
    _render_capped_numbered_actions(
        section.content,
        more_label=MORE_EXECUTIVE_ACTIONS_LABEL,
    )


def _render_collapsed_summary_section(section: NarrativeSection) -> None:
    with st.expander(section.title, expanded=False):
        st.markdown(section.content)


def _render_assessment_confidence(
    *,
    level_line: str,
    rationale: str,
) -> None:
    render_level2_heading(ASSESSMENT_CONFIDENCE_HEADING, zone=ZONE_EXECUTIVE)
    st.markdown('<div class="oic-confidence-block">', unsafe_allow_html=True)
    st.markdown(level_line)
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander(ASSESSMENT_CONFIDENCE_DETAILS_LABEL, expanded=False):
        st.markdown(rationale)


def render_executive_summary_content(result: AnalysisResult) -> None:
    """Render executive narrative content for the Executive Surface."""

    def body() -> None:
        narrative = result.narrative
        if narrative is None:
            st.info(NARRATIVE_DISABLED_MESSAGE)
            return

        st.markdown('<div class="oic-executive-briefing">', unsafe_allow_html=True)

        if narrative.executive_assessment is not None:
            st.markdown(
                format_executive_assessment_banner(narrative.executive_assessment),
                unsafe_allow_html=True,
            )

        for section in narrative.sections:
            if section.title in _COLLAPSED_SUMMARY_SECTIONS:
                _render_collapsed_summary_section(section)
                continue

            if section.title == ADVISOR_SECTION_EXECUTIVE_ACTIONS:
                _render_executive_actions_section(section)
                continue

            if section.title == ADVISOR_SECTION_KEY_MESSAGE:
                render_level2_heading(section.title, zone=ZONE_EXECUTIVE)
            else:
                st.markdown(f"##### {section.title}")
            st.markdown(section.content)

            if (
                section.title == ADVISOR_SECTION_KEY_MESSAGE
                and narrative.assessment_confidence is not None
            ):
                confidence = narrative.assessment_confidence
                _render_assessment_confidence(
                    level_line=format_assessment_confidence_level(confidence),
                    rationale=confidence.rationale,
                )

        with st.expander(LIMITATIONS_HEADING, expanded=False):
            st.markdown(narrative.limitations)

        st.markdown("</div>", unsafe_allow_html=True)

    render_section(EXECUTIVE_SUMMARY_HEADING, body, zone=ZONE_EXECUTIVE)


def render_recommended_actions(result: AnalysisResult) -> None:
    if not should_render_recommended_actions(result.report):
        return

    def body() -> None:
        humanised_steps = [
            humanise_report_text(result, step) for step in result.report.recommended_next_steps
        ]
        visible_steps = humanised_steps[:DEFAULT_INVESTIGATION_LIMIT]
        additional_steps = humanised_steps[DEFAULT_INVESTIGATION_LIMIT:]

        if visible_steps:
            render_numbered_items(visible_steps)

        if additional_steps:
            with st.expander(MORE_RECOMMENDATIONS_LABEL, expanded=False):
                render_numbered_items(additional_steps)

    render_section("Recommended Actions", body, zone=ZONE_EXECUTIVE)


def render_narrative_fallback_warnings(result: AnalysisResult) -> None:
    """Render compact narrative warnings on the Executive Surface when present."""
    for warning in result.narrative_warnings:
        st.warning(warning)
