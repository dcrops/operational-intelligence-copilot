"""Protocol for AI narrative generation."""

from __future__ import annotations

from typing import Protocol

from src.operational_intelligence.llm.narrative_models import NarrativeResponse, PromptArtifact


class NarrativeGenerator(Protocol):
    """Generate narrative communication from deterministic prompt artifacts."""

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return narrative communication for the given prompt artifact."""
        ...
