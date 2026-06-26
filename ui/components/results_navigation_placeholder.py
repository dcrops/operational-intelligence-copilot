"""Deprecated navigation placeholder retained for Milestone 13d reference only."""

from __future__ import annotations

import streamlit as st

from ui.results_headings import (
    SECTION_AUDIT,
    SECTION_INVESTIGATION,
    SECTION_OVERVIEW,
)

RESULTS_NAVIGATION_HEADING = "Results Navigation"


def render_results_navigation_placeholder() -> None:
    """Render non-interactive navigation labels (not used after Milestone 13c)."""
    st.markdown(f"#### {RESULTS_NAVIGATION_HEADING}")
    st.markdown(" | ".join((SECTION_OVERVIEW, SECTION_INVESTIGATION, SECTION_AUDIT)))
    st.caption("Interactive navigation will be available in a future milestone.")
    st.markdown("")
