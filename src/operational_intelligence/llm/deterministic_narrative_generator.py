"""Deterministic narrative generator for boundary validation and graceful fallback."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_briefing import (
    build_limitations_text,
    build_narrative_response,
)
from src.operational_intelligence.llm.narrative_models import NarrativeResponse, PromptArtifact

GENERATOR_TYPE = "deterministic"
LIMITATIONS = build_limitations_text(generator_type=GENERATOR_TYPE)


class DeterministicNarrativeGenerator:
    """Produce executive advisor sections from translated executive context."""

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return the same deterministic narrative for the same artifact."""
        return build_narrative_response(
            artifact.executive_context,
            generator_type=GENERATOR_TYPE,
            source_sections_used=artifact.source_sections,
            artifact_version=artifact.artifact_version,
        )
