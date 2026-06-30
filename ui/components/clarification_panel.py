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
    "analysis_type": (
        "This question could mean comparison analysis or anomaly detection. "
        "Which analysis would you like to run?"
    ),
    "comparison_direction": (
        "This question could refer to the highest or lowest value. "
        "Which comparison do you want?"
    ),
    "date_column": (
        "Multiple date columns are available for this dataset. "
        "Which date column should be used for this time period?"
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


def _format_clarification_option(option: str, clarification_type: str) -> str:
    if clarification_type in {"analysis_type", "comparison_direction"}:
        return option.replace("_", " ")
    return format_column_label(option)


def render_clarification(result: AnalysisResult) -> None:
    """Render a clarification prompt and allow the user to continue analysis."""
    clarification = result.clarification
    if clarification is None:
        return

    st.markdown('<div class="oic-clarification-panel">', unsafe_allow_html=True)
    st.subheader("Clarification Required")
    st.write(_clarification_message(clarification.clarification_type))
    st.caption("Select an option below to continue the analysis.")

    clarification_type = clarification.clarification_type
    selected = st.radio(
        "Clarification options",
        options=clarification.options,
        format_func=lambda option: _format_clarification_option(option, clarification_type),
        label_visibility="collapsed",
        key=f"clarification_{clarification_type}",
    )

    if st.button("Continue analysis", type="primary", key="continue_clarification"):
        prior_metrics = list(result.request.selected_metrics or [])
        prior_dimensions = list(result.request.selected_dimensions or [])
        prior_comparison_direction = result.request.selected_comparison_direction
        prior_date_column = result.request.selected_date_column
        selected_metrics = prior_metrics or None
        selected_dimensions = prior_dimensions or None
        selected_comparison_direction = prior_comparison_direction
        selected_date_column = prior_date_column
        requested_analysis_type = result.request.requested_analysis_type

        if clarification_type == "metric":
            selected_metrics = [selected]
        elif clarification_type in {"dimension", "comparison_target"}:
            selected_dimensions = [selected]
        elif clarification_type == "analysis_type":
            requested_analysis_type = selected
        elif clarification_type == "comparison_direction":
            selected_comparison_direction = selected
        elif clarification_type == "date_column":
            selected_date_column = selected

        try:
            with st.spinner("Running analysis..."):
                continued_result = run_analysis(
                    question=result.request.question,
                    df=st.session_state.df,
                    profile=st.session_state.profile,
                    selected_metrics=selected_metrics,
                    selected_dimensions=selected_dimensions,
                    selected_comparison_direction=selected_comparison_direction,
                    selected_date_column=selected_date_column,
                    requested_analysis_type=requested_analysis_type,
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
    st.markdown("</div>", unsafe_allow_html=True)
