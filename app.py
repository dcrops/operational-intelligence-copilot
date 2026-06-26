import logging

import streamlit as st

from ui.analysis_service import run_analysis
from ui.components.clarification_panel import render_clarification
from ui.components.results_panel import render_results
from ui.components.app_shell import render_app_hero
from ui.components.upload import render_sidebar
from ui.narrative_runtime import get_narrative_runtime_config
from ui.state import has_dataset, init_session_state, set_analysis_error, set_analysis_result

EXAMPLE_QUESTIONS_BY_DATASET = {
    "workforce_demo": [
        "What looks unusual and what should I investigate?",
        "How have hours changed over time?",
        "Which department has the highest hours?",
        "Analyse this dataset",
    ],
    "manufacturing_demo": [
        "What looks unusual and what should I investigate?",
        "How has downtime changed over time?",
        "Which production line has the highest defects?",
        "Analyse this dataset",
    ],
    "education_demo": [
        "What looks unusual and what should I investigate?",
        "How has attendance changed over time?",
        "Which school has the highest behaviour incidents?",
        "Analyse this dataset",
    ],
}
DEFAULT_EXAMPLE_QUESTIONS = [
    "What looks unusual and what should I investigate?",
    "How has this metric changed over time?",
    "Which group has the highest values?",
    "Analyse this dataset",
]

PREVIEW_ROW_LIMIT = 50


def _example_questions_for_dataset(dataset_name: str) -> list[str]:
    return EXAMPLE_QUESTIONS_BY_DATASET.get(dataset_name, DEFAULT_EXAMPLE_QUESTIONS)


def _question_placeholder_for_dataset(dataset_name: str) -> str:
    placeholders = {
        "workforce_demo": "Which department has the highest hours?",
        "manufacturing_demo": "Which production line has the highest defects?",
        "education_demo": "Which school has the highest behaviour incidents?",
    }
    return placeholders.get(dataset_name, "Ask a question about this dataset...")


st.set_page_config(
    page_title="Operational Intelligence Copilot",
    page_icon="📊",
    layout="wide",
)

init_session_state()
render_app_hero()
render_sidebar()

if not has_dataset():
    st.info("Upload a CSV in the sidebar or load a sample dataset to get started.")
    st.stop()

dataset_name = st.session_state.dataset_name
example_questions = _example_questions_for_dataset(dataset_name)

def _render_dataset_preview() -> None:
    df = st.session_state.df
    st.dataframe(df.head(PREVIEW_ROW_LIMIT), use_container_width=True)
    if len(df) > PREVIEW_ROW_LIMIT:
        st.caption(f"Showing first {PREVIEW_ROW_LIMIT} of {len(df)} rows.")
    else:
        st.caption(f"Showing all {len(df)} rows.")


last_result = st.session_state.get("last_result")
collapse_dataset_preview = (
    last_result is not None and last_result.clarification is None
)

if collapse_dataset_preview:
    with st.expander("Dataset Preview", expanded=False):
        _render_dataset_preview()
else:
    st.subheader("Dataset Preview")
    _render_dataset_preview()

st.subheader("Ask a Question")
st.caption("Example questions:")
example_cols = st.columns(len(example_questions))
for index, example in enumerate(example_questions):
    if example_cols[index].button(example, key=f"example_{index}"):
        st.session_state.question = example

st.text_area(
    "Your question",
    key="question",
    placeholder=_question_placeholder_for_dataset(dataset_name),
)

if st.button(
    "Analyze",
    type="primary",
    disabled=not st.session_state.question.strip(),
    key="analyze_question",
):
    try:
        with st.spinner("Running analysis..."):
            result = run_analysis(
                question=st.session_state.question,
                df=st.session_state.df,
                profile=st.session_state.profile,
                narrative_config=get_narrative_runtime_config(),
            )
        set_analysis_result(result)
        st.rerun()
    except ValueError as exc:
        set_analysis_error(str(exc))
    except Exception:
        logging.exception("Analysis run failed")
        set_analysis_error(
            "Something went wrong while running the analysis. "
            "Please check your dataset and try again."
        )

if st.session_state.last_error:
    st.error(st.session_state.last_error)

if st.session_state.last_result:
    if st.session_state.last_result.clarification is not None:
        render_clarification(st.session_state.last_result)
    else:
        render_results(st.session_state.last_result)
