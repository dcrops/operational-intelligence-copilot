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
st.dataframe(st.session_state.df, use_container_width=True)

st.subheader("Ask a Question")
st.caption("Example questions:")
example_cols = st.columns(len(EXAMPLE_QUESTIONS))
for index, example in enumerate(EXAMPLE_QUESTIONS):
    if example_cols[index].button(example, key=f"example_{index}"):
        st.session_state.question = example

question = st.text_area(
    "Your question",
    key="question",
    placeholder="Which department has the highest hours?",
)

if st.button("Analyze", type="primary"):
    try:
        result = run_analysis(
            question=question,
            df=st.session_state.df,
            profile=st.session_state.profile,
        )
        set_analysis_result(result)
    except ValueError as exc:
        set_analysis_error(str(exc))

if st.session_state.last_error:
    st.error(st.session_state.last_error)

if st.session_state.last_result:
    render_results(st.session_state.last_result)
