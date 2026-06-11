from pathlib import Path

import pandas as pd
import streamlit as st

from src.operational_intelligence.profiling import DatasetProfiler
from ui.state import set_dataset

SAMPLE_DATASET_PATH = Path("data/sample/workforce_demo.csv")


def render_sidebar() -> None:
    st.sidebar.header("Dataset")

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        source_id = f"upload:{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state.get("loaded_source_id") != source_id:
            try:
                df = pd.read_csv(uploaded_file)
                if df.empty:
                    st.sidebar.error("The uploaded CSV is empty.")
                else:
                    dataset_name = Path(uploaded_file.name).stem or "uploaded_dataset"
                    profile = DatasetProfiler().profile_dataframe(dataset_name, df)
                    set_dataset(df, dataset_name, profile)
                    st.session_state.loaded_source_id = source_id
                    st.sidebar.success(f"Loaded {dataset_name}.")
            except Exception as exc:
                st.sidebar.error(f"Could not read CSV: {exc}")

    if st.sidebar.button("Load sample dataset"):
        if not SAMPLE_DATASET_PATH.exists():
            st.sidebar.error(
                f"Sample dataset not found at `{SAMPLE_DATASET_PATH}`. "
                "Upload a CSV file instead."
            )
        else:
            source_id = f"sample:{SAMPLE_DATASET_PATH}"
            if st.session_state.get("loaded_source_id") != source_id:
                try:
                    df = pd.read_csv(SAMPLE_DATASET_PATH)
                    profile = DatasetProfiler().profile_dataframe("workforce_demo", df)
                    set_dataset(df, "workforce_demo", profile)
                    st.session_state.loaded_source_id = source_id
                    st.sidebar.success("Loaded sample dataset.")
                except Exception as exc:
                    st.sidebar.error(f"Could not load sample dataset: {exc}")

    profile = st.session_state.get("profile")
    if profile is not None:
        st.sidebar.divider()
        st.sidebar.subheader("Profile summary")
        st.sidebar.metric("Rows", profile.row_count)
        st.sidebar.metric("Columns", profile.column_count)
        st.sidebar.metric("Missing values", profile.missing_value_count)
        st.sidebar.caption(f"Metrics: {', '.join(profile.potential_metrics) or 'None'}")
        st.sidebar.caption(
            f"Dimensions: {', '.join(profile.potential_dimensions) or 'None'}"
        )
        st.sidebar.caption(f"Suitable tools: {', '.join(profile.suitable_tools) or 'None'}")
