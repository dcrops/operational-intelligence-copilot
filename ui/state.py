from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from src.operational_intelligence.models import DatasetProfile

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
        "loaded_source_id": None,
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
