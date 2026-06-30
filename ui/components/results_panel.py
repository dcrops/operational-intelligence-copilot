"""Results panel orchestration for the executive results information architecture."""

from __future__ import annotations

import streamlit as st

from ui.components.analysis_header import render_analysis_header
from ui.components.results_audit import render_audit_bundle
from ui.components.results_executive import (
    render_direct_answer,
    render_executive_summary_content,
    render_narrative_fallback_warnings,
    render_recommended_actions,
)
from ui.components.results_investigation import render_findings_bundle
from ui.models import AnalysisResult
from ui.results_headings import TAB_AUDIT_LABEL, TAB_FINDINGS_LABEL, TAB_SUMMARY_LABEL
from ui.results_presentation import inject_results_styles
from ui.state import RESULTS_TABS_SESSION_KEY


def render_results(result: AnalysisResult) -> None:
    """Render analysis header and task-oriented results tabs."""
    inject_results_styles()
    render_analysis_header(result)

    summary_tab, findings_tab, audit_tab = st.tabs(
        [TAB_SUMMARY_LABEL, TAB_FINDINGS_LABEL, TAB_AUDIT_LABEL],
        key=RESULTS_TABS_SESSION_KEY,
        default=TAB_SUMMARY_LABEL,
        on_change="rerun",
    )

    with summary_tab:
        render_direct_answer(result)
        render_executive_summary_content(result)
        render_recommended_actions(result)
        render_narrative_fallback_warnings(result)

    with findings_tab:
        render_findings_bundle(result)

    with audit_tab:
        render_audit_bundle(result)
