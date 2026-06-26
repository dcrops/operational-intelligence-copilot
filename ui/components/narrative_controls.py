"""Sidebar controls for executive narrative provider selection."""

from __future__ import annotations

import streamlit as st

from src.operational_intelligence.llm.narrative_factory import describe_provider_status
from src.operational_intelligence.llm.narrative_provider_registry import provider_display_name
from src.operational_intelligence.llm.narrative_config import PROVIDER_DETERMINISTIC, PROVIDER_OPENAI
from ui.narrative_runtime import (
    NARRATIVE_PROVIDER_OPTIONS,
    format_narrative_mode_label,
    get_narrative_runtime_config,
)


def render_narrative_controls() -> None:
    """Render executive summary provider selection and provider status."""
    st.sidebar.divider()
    st.sidebar.subheader("Executive Summary")

    st.sidebar.radio(
        "Narrative Provider",
        options=NARRATIVE_PROVIDER_OPTIONS,
        format_func=format_narrative_mode_label,
        key="narrative_mode",
    )

    st.sidebar.caption(
        f"**{provider_display_name(PROVIDER_DETERMINISTIC)}** — "
        "Uses deterministic executive narrative generation. No API key is required."
    )
    st.sidebar.caption(
        f"**{provider_display_name(PROVIDER_OPENAI)}** — "
        "Uses the configured OpenAI provider when available."
    )

    config = get_narrative_runtime_config()
    status_level, status_message = describe_provider_status(config)
    if status_level == "active":
        st.sidebar.success(f"🟢 {status_message}")
    elif status_level == "warning":
        st.sidebar.warning(f"🟡 {status_message}")

    st.sidebar.caption("Applies to the next analysis run.")
