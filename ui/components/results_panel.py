"""Results panel orchestration for the executive results information architecture."""

from __future__ import annotations

import streamlit as st

from ui.components.analysis_header import render_analysis_header
from ui.components.results_audit import render_audit_content
from ui.components.results_executive import (
    render_direct_answer,
    render_executive_summary_content,
    render_recommended_actions,
)
from ui.components.results_investigation import render_investigation_content, render_overview_content
from ui.components.results_navigation_placeholder import render_results_navigation_placeholder
from ui.models import AnalysisResult
from ui.results_headings import SECTION_OVERVIEW


def render_results(result: AnalysisResult) -> None:
    """Render analysis results in the approved task-oriented information hierarchy."""
    render_analysis_header(result)
    render_direct_answer(result)
    render_executive_summary_content(result)
    render_recommended_actions(result)
    render_results_navigation_placeholder()

    st.markdown(f"#### {SECTION_OVERVIEW}")
    render_overview_content(result)

    render_investigation_content(result)
    render_audit_content(result)
