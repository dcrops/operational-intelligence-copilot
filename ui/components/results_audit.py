"""Audit results content: transparency, provider verification, and governance."""

from __future__ import annotations

import streamlit as st

from ui.models import AnalysisResult
from ui.narrative_presentation import (
    GENERATED_BY_HEADING,
    GOVERNANCE_CAPTION,
    TECHNICAL_DETAILS_HEADING,
    format_generated_by_secondary_metadata,
    format_generation_details,
    format_generation_method,
)
from ui.results_presentation import ZONE_AUDIT, render_section, render_subsection
from ui.transparency import (
    format_auto_resolved_trail,
    format_clarification_trail,
    format_metrics_analysed_trail,
    format_snapshot_contributors_trail,
    format_snapshot_trail,
    format_temporal_filter_trail,
)


def _render_generated_by(result: AnalysisResult) -> None:
    narrative = result.narrative
    if narrative is None or narrative.generation_metadata is None:
        return

    status_level, provider_label = format_generation_method(narrative.generation_metadata)
    st.markdown(f"**{GENERATED_BY_HEADING}**")
    if status_level == "warning":
        st.warning(f"🟡 {provider_label}")
    else:
        st.success(f"🟢 {provider_label}")
    for line in format_generated_by_secondary_metadata(narrative.generation_metadata):
        st.caption(line)


def _render_runtime_metadata(result: AnalysisResult) -> None:
    for warning in result.narrative_warnings:
        st.warning(warning)


def _render_governance_information() -> None:
    st.caption(GOVERNANCE_CAPTION)


def _render_technical_details(result: AnalysisResult) -> None:
    narrative = result.narrative
    if narrative is None:
        return

    generation_details = format_generation_details(narrative)
    if not generation_details:
        return

    with st.expander(TECHNICAL_DETAILS_HEADING):
        for line in generation_details:
            st.caption(f"- {line}")


def render_audit_bundle(result: AnalysisResult) -> None:
    """Render audit and verification content inside a disclosure group."""
    st.markdown('<div class="oic-audit-body">', unsafe_allow_html=True)

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

    render_section("System Transparency", render_transparency, zone=ZONE_AUDIT)

    def render_verification() -> None:
        st.markdown('<div class="oic-audit-verification">', unsafe_allow_html=True)
        st.markdown('<div class="oic-audit-generated-by">', unsafe_allow_html=True)
        _render_generated_by(result)
        st.markdown("</div>", unsafe_allow_html=True)
        _render_runtime_metadata(result)
        _render_technical_details(result)
        _render_governance_information()
        st.markdown("</div>", unsafe_allow_html=True)

    render_subsection("Verification", render_verification, zone=ZONE_AUDIT, bordered=False)
    st.markdown("</div>", unsafe_allow_html=True)
