"""Pure presentation helpers for AI-assisted executive narrative in the UI."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import (
    AssessmentConfidencePresentation,
    ExecutiveAssessmentBanner,
    NarrativeResponse,
)

EXECUTIVE_NARRATIVE_AI_ASSISTED_HEADING = "Executive Narrative (AI-Assisted)"
EXECUTIVE_ASSESSMENT_HEADING = "Executive Assessment"
ASSESSMENT_CONFIDENCE_HEADING = "Assessment Confidence"
LIMITATIONS_HEADING = "Limitations"
TECHNICAL_DETAILS_HEADING = "Technical Details"

NARRATIVE_DISABLED_MESSAGE = (
    "AI-assisted narrative is not enabled. "
    "The deterministic analysis above is the authoritative answer."
)

GOVERNANCE_CAPTION = (
    "This AI-assisted executive advisor summarises the deterministic analysis above "
    "and suggests where to investigate. "
    "It does not replace Direct Answer, Executive Reasoning, or System Transparency."
)

_BANNER_ACCENT_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#16a34a",
    "stable": "#16a34a",
}


def format_executive_assessment_banner(banner: ExecutiveAssessmentBanner) -> str:
    """Return markdown with severity accent styling for the executive assessment banner."""
    accent = _BANNER_ACCENT_COLORS.get(banner.level.lower(), "#64748b")
    indicator = banner.indicator.strip()
    headline = banner.headline.strip()
    return (
        f'<div style="border-left: 4px solid {accent}; padding: 0.75rem 1rem; '
        f'margin: 0.5rem 0 1rem 0; background-color: rgba(148, 163, 184, 0.08);">'
        f"<strong>{indicator} {EXECUTIVE_ASSESSMENT_HEADING}</strong><br><br>"
        f"{headline}"
        f"</div>"
    )


def format_assessment_confidence_level(
    confidence: AssessmentConfidencePresentation,
) -> str:
    """Return a compact confidence level line with optional indicator."""
    indicator = confidence.indicator.strip()
    level = confidence.level.strip()
    if indicator:
        return f"{indicator} **{level}**"
    return f"**{level}**"


def format_generation_details(narrative: NarrativeResponse) -> tuple[str, ...]:
    """Return caption-ready generation detail lines for available metadata only."""
    lines: list[str] = []

    if narrative.generator_type:
        lines.append(f"Generator: {narrative.generator_type}")

    if narrative.model is not None:
        lines.append(f"Model: {narrative.model}")

    if narrative.generation_duration_ms is not None:
        lines.append(f"Duration: {narrative.generation_duration_ms} ms")

    if narrative.artifact_version is not None:
        lines.append(f"Artifact version: {narrative.artifact_version}")

    return tuple(lines)
