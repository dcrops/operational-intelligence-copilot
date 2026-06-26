"""Results panel orchestration for the executive results information architecture."""

from __future__ import annotations

from ui.components.analysis_header import render_analysis_header
from ui.components.results_audit import render_audit_bundle
from ui.components.results_executive import (
    render_direct_answer,
    render_executive_summary_content,
    render_narrative_fallback_warnings,
    render_recommended_actions,
)
from ui.components.results_investigation import render_investigation_bundle
from ui.models import AnalysisResult
from ui.results_headings import DISCLOSURE_AUDIT_LABEL, DISCLOSURE_INVESTIGATION_LABEL
from ui.results_presentation import (
    ZONE_AUDIT,
    ZONE_INVESTIGATION,
    inject_results_styles,
    render_collapsible_group,
)


def render_results(result: AnalysisResult) -> None:
    """Render the Executive Surface and collapsed disclosure groups."""
    inject_results_styles()
    render_analysis_header(result)
    render_direct_answer(result)
    render_executive_summary_content(result)
    render_recommended_actions(result)
    render_narrative_fallback_warnings(result)

    render_collapsible_group(
        DISCLOSURE_INVESTIGATION_LABEL,
        lambda: render_investigation_bundle(result),
        zone=ZONE_INVESTIGATION,
    )
    render_collapsible_group(
        DISCLOSURE_AUDIT_LABEL,
        lambda: render_audit_bundle(result),
        zone=ZONE_AUDIT,
    )
