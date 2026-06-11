import streamlit as st

from src.operational_intelligence.models import Finding
from ui.models import AnalysisResult


def _render_findings(title: str, findings: list[Finding]) -> None:
    st.markdown(f"**{title}**")
    if not findings:
        st.caption("None.")
        return

    for finding in findings:
        line = f"- **[{finding.severity}]** {finding.title}"
        if finding.description:
            line += f": {finding.description}"
        st.markdown(line)


def render_results(result: AnalysisResult) -> None:
    st.subheader("Results")

    with st.container(border=True):
        st.markdown("**Deterministic Answer**")
        st.markdown(result.deterministic_answer)

    with st.container(border=True):
        st.markdown("**Executive Summary**")
        st.markdown(result.report.executive_summary)

    with st.container(border=True):
        st.markdown("**Findings by Priority**")
        _render_findings("High Priority", result.report.high_priority_findings)
        _render_findings("Medium Priority", result.report.medium_priority_findings)
        _render_findings("Low Priority", result.report.low_priority_findings)

    with st.container(border=True):
        st.markdown("**Recommended Next Steps**")
        if result.report.recommended_next_steps:
            for step in result.report.recommended_next_steps:
                st.markdown(f"- {step}")
        else:
            st.caption("None.")

    st.caption(f"Routed tools: {', '.join(result.routes)}")

    with st.container(border=True):
        st.markdown("**LLM Explanation**")
        st.info("LLM explanations are not enabled yet. Deterministic analysis is shown above.")
