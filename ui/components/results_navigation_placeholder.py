"""Placeholder for future results navigation (Milestone 13c+)."""

from __future__ import annotations

import streamlit as st

from ui.results_headings import (
    RESULTS_NAVIGATION_HEADING,
    RESULTS_NAVIGATION_PLACEHOLDER_LABELS,
)


def render_results_navigation_placeholder() -> None:
    """Render non-interactive navigation labels for the approved IA structure."""
    st.markdown(f"#### {RESULTS_NAVIGATION_HEADING}")
    st.markdown(" | ".join(RESULTS_NAVIGATION_PLACEHOLDER_LABELS))
    st.caption("Interactive navigation will be available in a future milestone.")
    st.markdown("")
