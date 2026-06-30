from pathlib import Path

import pandas as pd
import streamlit as st

from src.operational_intelligence.profiling import DatasetProfiler
from ui.components.app_shell import render_sidebar_branding
from ui.components.narrative_controls import render_narrative_controls
from ui.state import set_dataset

SAMPLE_DATASETS = {
    "Workforce demo": {
        "path": Path("data/sample/workforce_demo_v2.csv"),
        "dataset_name": "workforce_demo",
    },
    "Manufacturing demo": {
        "path": Path("data/sample/manufacturing_demo.csv"),
        "dataset_name": "manufacturing_demo",
    },
    "Education demo": {
        "path": Path("data/sample/education_demo.csv"),
        "dataset_name": "education_demo",
    },
}


def _load_sample_dataset(label: str) -> None:
    sample = SAMPLE_DATASETS[label]
    sample_path = sample["path"]
    dataset_name = sample["dataset_name"]

    if not sample_path.exists():
        st.sidebar.error(
            f"Sample dataset not found at `{sample_path}`. "
            "Run the generator script or upload a CSV file instead."
        )
        return

    source_id = f"sample:{sample_path}"
    if st.session_state.get("loaded_source_id") == source_id:
        return

    try:
        df = pd.read_csv(sample_path)
        profile = DatasetProfiler().profile_dataframe(dataset_name, df)
        set_dataset(df, dataset_name, profile)
        st.session_state.loaded_source_id = source_id
        st.session_state.sample_dataset_label = label
        st.sidebar.success(f"Loaded {label}.")
    except Exception as exc:
        st.sidebar.error(f"Could not load {label}: {exc}")


def render_sidebar() -> None:
    render_sidebar_branding()
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
                    st.session_state.sample_dataset_label = None
                    st.sidebar.success(f"Loaded {dataset_name}.")
            except Exception as exc:
                st.sidebar.error(f"Could not read CSV: {exc}")

    st.sidebar.subheader("Sample datasets")
    sample_labels = list(SAMPLE_DATASETS.keys())
    selected_sample = st.sidebar.selectbox(
        "Choose a sample dataset",
        sample_labels,
        key="sample_dataset_choice",
    )

    if st.sidebar.button("Load selected sample"):
        with st.sidebar.spinner(f"Loading {selected_sample}..."):
            _load_sample_dataset(selected_sample)

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

    render_narrative_controls()
