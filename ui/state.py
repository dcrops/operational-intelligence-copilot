from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from src.operational_intelligence.models import DatasetProfile
from ui.narrative_runtime import narrative_mode_from_environment
from ui.results_headings import TAB_SUMMARY_LABEL

RESULTS_TABS_SESSION_KEY = "results_tabs"

if TYPE_CHECKING:
    from ui.models import AnalysisResult


def init_session_state() -> None:
    defaults = {
        "df": None,
        "dataset_name": "",
        "profile": None,
        "last_result": None,
        "last_error": None,
        "question": "",
        "pending_question": "",
        "scroll_to_question_pending": False,
        "loaded_source_id": None,
        "narrative_mode": narrative_mode_from_environment(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def has_dataset() -> bool:
    df = st.session_state.get("df")
    profile = st.session_state.get("profile")
    return isinstance(df, pd.DataFrame) and not df.empty and isinstance(profile, DatasetProfile)


def set_dataset(df: pd.DataFrame, dataset_name: str, profile: DatasetProfile) -> None:
    st.session_state.df = df
    st.session_state.dataset_name = dataset_name
    st.session_state.profile = profile
    st.session_state.last_result = None
    st.session_state.last_error = None


def set_analysis_result(result: AnalysisResult | None) -> None:
    st.session_state.last_result = result
    st.session_state.last_error = None


def set_analysis_error(message: str) -> None:
    st.session_state.last_error = message
    st.session_state.last_result = None


def apply_suggested_question(question: str) -> None:
    """Stage a suggested follow-up for the main question input on the next rerun."""
    st.session_state.pending_question = question.strip()
    st.session_state.scroll_to_question_pending = True
    st.rerun()


def reset_results_tab_to_summary() -> None:
    """Return the results panel to the Summary tab after a new analysis."""
    st.session_state[RESULTS_TABS_SESSION_KEY] = TAB_SUMMARY_LABEL


def consume_pending_question() -> None:
    """Apply a staged follow-up question before the question widget is rendered."""
    pending = st.session_state.get("pending_question", "")
    if pending:
        st.session_state.question = pending
        st.session_state.pending_question = ""
