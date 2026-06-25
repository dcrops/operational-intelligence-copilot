"""Pure presentation helpers for AI-assisted executive narrative in the UI."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import NarrativeResponse

EXECUTIVE_NARRATIVE_AI_ASSISTED_HEADING = "Executive Narrative (AI-Assisted)"
KEY_MESSAGE_HEADING = "Key Message"
EXECUTIVE_NARRATIVE_HEADING = "Executive Narrative"
LIMITATIONS_HEADING = "Limitations"
GENERATION_DETAILS_HEADING = "Generation Details"

NARRATIVE_DISABLED_MESSAGE = (
    "AI-assisted narrative is not enabled. "
    "The deterministic analysis above is the authoritative answer."
)

GOVERNANCE_CAPTION = (
    "This AI-assisted narrative summarises the deterministic analysis above. "
    "It does not replace Direct Answer, Executive Reasoning, or System Transparency."
)


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
