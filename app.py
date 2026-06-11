import logging

import streamlit as st

from ui.analysis_service import run_analysis
from ui.components.results_panel import render_results
from ui.components.upload import render_sidebar
from ui.state import has_dataset, init_session_state, set_analysis_error, set_analysis_result

EXAMPLE_QUESTIONS = [
    "What looks unusual and what should I investigate?",
    "How has hours changed over time?",
    "Which department has the highest hours?",
    "Analyse this dataset",
]

PREVIEW_ROW_LIMIT = 50


st.set_page_config(
    page_title="Operational Intelligence Copilot",
    page_icon="📊",
    layout="wide",
)

init_session_state()
render_sidebar()

st.title("Operational Intelligence Copilot")
st.write(
    "Upload operational data, ask a natural language question, and review "
    "deterministic findings from the analysis pipeline."
)

if not has_dataset():
    st.info("Upload a CSV in the sidebar or load the sample dataset to get started.")
    st.stop()

st.subheader("Dataset Preview")
df = st.session_state.df
st.dataframe(df.head(PREVIEW_ROW_LIMIT), use_container_width=True)
if len(df) > PREVIEW_ROW_LIMIT:
    st.caption(f"Showing first {PREVIEW_ROW_LIMIT} of {len(df)} rows.")
else:
    st.caption(f"Showing all {len(df)} rows.")

st.subheader("Ask a Question")
st.caption("Example questions:")
example_cols = st.columns(len(EXAMPLE_QUESTIONS))
for index, example in enumerate(EXAMPLE_QUESTIONS):
    if example_cols[index].button(example, key=f"example_{index}"):
        st.session_state.question = example

st.text_area(
    "Your question",
    key="question",
    placeholder="Which department has the highest hours?",
)

if st.button(
    "Analyze",
    type="primary",
    disabled=not st.session_state.question.strip(),
):
    try:
        with st.spinner("Running analysis..."):
            result = run_analysis(
                question=st.session_state.question,
                df=st.session_state.df,
                profile=st.session_state.profile,
            )
        set_analysis_result(result)
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
    render_results(st.session_state.last_result)
