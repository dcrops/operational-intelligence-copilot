"""Streamlit runtime narrative provider mapping and session-backed configuration."""

from __future__ import annotations

import streamlit as st

from src.operational_intelligence.llm.narrative_config import (
    PROVIDER_DETERMINISTIC,
    PROVIDER_OPENAI,
    NarrativeRuntimeConfig,
)
from src.operational_intelligence.llm.narrative_provider_registry import provider_display_name

# Internal session values (stable provider IDs).
NARRATIVE_MODE_OFF = "off"
NARRATIVE_MODE_DETERMINISTIC = PROVIDER_DETERMINISTIC
NARRATIVE_MODE_OPENAI = PROVIDER_OPENAI

NARRATIVE_PROVIDER_OPTIONS: tuple[str, ...] = (
    NARRATIVE_MODE_DETERMINISTIC,
    NARRATIVE_MODE_OPENAI,
)

# Backward-compatible aliases used by tests and legacy imports.
NARRATIVE_MODE_OPTIONS = NARRATIVE_PROVIDER_OPTIONS


def narrative_mode_from_environment() -> str:
    """Map environment defaults to the internal sidebar provider value."""
    config = NarrativeRuntimeConfig.from_environment()
    if config.enabled and config.provider == PROVIDER_OPENAI:
        return NARRATIVE_MODE_OPENAI
    return NARRATIVE_MODE_DETERMINISTIC


def narrative_mode_to_config(mode: str) -> NarrativeRuntimeConfig:
    """Convert a sidebar provider value to runtime narrative configuration."""
    if mode == NARRATIVE_MODE_OFF:
        return NarrativeRuntimeConfig.disabled()
    if mode == NARRATIVE_MODE_OPENAI:
        return NarrativeRuntimeConfig.openai()
    return NarrativeRuntimeConfig.deterministic()


def get_narrative_runtime_config() -> NarrativeRuntimeConfig:
    """Return narrative configuration from authoritative Streamlit session state."""
    mode = st.session_state.get("narrative_mode", NARRATIVE_MODE_DETERMINISTIC)
    if mode not in NARRATIVE_PROVIDER_OPTIONS:
        mode = NARRATIVE_MODE_DETERMINISTIC
    return narrative_mode_to_config(mode)


def format_narrative_mode_label(mode: str) -> str:
    """Return the user-facing label for an internal narrative provider value."""
    if mode == NARRATIVE_MODE_OPENAI:
        return provider_display_name(PROVIDER_OPENAI)
    if mode == NARRATIVE_MODE_DETERMINISTIC:
        return provider_display_name(PROVIDER_DETERMINISTIC)
    return provider_display_name(PROVIDER_DETERMINISTIC)
