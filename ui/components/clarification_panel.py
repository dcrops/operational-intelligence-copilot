import streamlit as st

from ui.analysis_service import run_analysis
from ui.formatting import format_column_label
from ui.models import AnalysisResult
from ui.state import set_analysis_result

_CLARIFICATION_MESSAGES = {
    "metric": (
        "Multiple metrics are available for this dataset. "
        "Which metric would you like to analyse?"
    ),
    "dimension": (
        "Multiple grouping fields are available for this dataset. "
        "Which one would you like to compare?"
    ),
    "comparison_target": (
        "Multiple grouping fields are available for this dataset. "
        "Which one would you like to compare?"
    ),
}
_DEFAULT_CLARIFICATION_MESSAGE = (
    "I need one more detail before I can run the analysis."
)


def _clarification_message(clarification_type: str) -> str:
    return _CLARIFICATION_MESSAGES.get(
        clarification_type,
        _DEFAULT_CLARIFICATION_MESSAGE,
    )


def render_clarification(result: AnalysisResult) -> None:
    """Render a clarification prompt and allow the user to continue analysis."""
    clarification = result.clarification
    if clarification is None:
        return

    st.subheader("Clarification Required")
    st.write(_clarification_message(clarification.clarification_type))
    st.caption("Select an option below to continue the analysis.")

    selected = st.radio(
        "Clarification options",
        options=clarification.options,
        format_func=format_column_label,
        label_visibility="collapsed",
        key=f"clarification_{clarification.clarification_type}",
    )

    if st.button("Continue analysis", type="primary", key="continue_clarification"):
        prior_metrics = list(result.request.selected_metrics or [])
        prior_dimensions = list(result.request.selected_dimensions or [])
        selected_metrics = prior_metrics or None
        selected_dimensions = prior_dimensions or None

        if clarification.clarification_type == "metric":
            selected_metrics = [selected]
        elif clarification.clarification_type in {"dimension", "comparison_target"}:
            selected_dimensions = [selected]

        try:
            with st.spinner("Running analysis..."):
                continued_result = run_analysis(
                    question=result.request.question,
                    df=st.session_state.df,
                    profile=st.session_state.profile,
                    selected_metrics=selected_metrics,
                    selected_dimensions=selected_dimensions,
                )
            set_analysis_result(continued_result)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "Something went wrong while running the analysis. "
                "Please check your dataset and try again."
            )
