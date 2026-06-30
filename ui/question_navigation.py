"""Question input anchor and scroll helpers for guided follow-up workflow."""

from __future__ import annotations

import streamlit as st

QUESTION_ANCHOR_ID = "ask-question"


def render_question_anchor() -> None:
    """Render a stable anchor target for returning to the question input area."""
    st.markdown(
        f'<div id="{QUESTION_ANCHOR_ID}" class="oic-question-anchor"></div>',
        unsafe_allow_html=True,
    )


def scroll_to_question_if_pending() -> None:
    """Smoothly scroll to the question input when a follow-up question was selected."""
    if not st.session_state.get("scroll_to_question_pending"):
        return
    st.session_state.scroll_to_question_pending = False
    st.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            const target = doc.getElementById("{QUESTION_ANCHOR_ID}");
            if (target) {{
                target.scrollIntoView({{ behavior: "smooth", block: "start" }});
            }}
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )
