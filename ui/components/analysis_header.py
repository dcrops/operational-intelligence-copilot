"""Analysis Header — context shown before executive results content."""

from __future__ import annotations

from ui.models import AnalysisResult
from ui.narrative_presentation import format_generation_method
from ui.results_headings import ANALYSIS_HEADER_STATUS
from ui.results_presentation import render_metadata_header


def _dataset_name(result: AnalysisResult) -> str:
    if result.request.dataset_names:
        return result.request.dataset_names[0]
    return "Unknown dataset"


def _narrative_provider_line(result: AnalysisResult) -> str | None:
    narrative = result.narrative
    if narrative is None or narrative.generation_metadata is None:
        return None

    _, provider_label = format_generation_method(narrative.generation_metadata)
    return provider_label


def render_analysis_header(result: AnalysisResult) -> None:
    """Render compact analysis metadata before executive results content."""
    rows: list[tuple[str, str]] = [
        ("Question", result.request.question),
        ("Dataset", _dataset_name(result)),
    ]

    if result.completed_at is not None:
        rows.append(("Completed", result.completed_at.strftime("%Y-%m-%d %H:%M:%S")))

    provider_line = _narrative_provider_line(result)
    if provider_line is not None:
        rows.append(("Narrative Provider", provider_line))

    render_metadata_header(status=ANALYSIS_HEADER_STATUS, rows=tuple(rows))
