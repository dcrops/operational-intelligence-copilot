"""Analysis Header — context shown before executive results content."""

from __future__ import annotations

import streamlit as st

from ui.models import AnalysisResult
from ui.narrative_presentation import format_generation_method
from ui.results_headings import ANALYSIS_HEADER_STATUS


def _dataset_name(result: AnalysisResult) -> str:
    if result.request.dataset_names:
        return result.request.dataset_names[0]
    return "Unknown dataset"


def _narrative_provider_line(result: AnalysisResult) -> str | None:
    narrative = result.narrative
    if narrative is None or narrative.generation_metadata is None:
        return None

    _, provider_label = format_generation_method(narrative.generation_metadata)
    return provider_label


def render_analysis_header(result: AnalysisResult) -> None:
    """Render analysis context: status, question, dataset, timestamp, and provider."""
    st.markdown(f"#### {ANALYSIS_HEADER_STATUS}")

    with st.container(border=True):
        st.markdown(f"**Question:** {result.request.question}")
        st.markdown(f"**Dataset:** {_dataset_name(result)}")

        if result.completed_at is not None:
            st.markdown(f"**Completed:** {result.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        provider_line = _narrative_provider_line(result)
        if provider_line is not None:
            st.markdown(f"**Narrative provider:** {provider_line}")

    st.markdown("")
