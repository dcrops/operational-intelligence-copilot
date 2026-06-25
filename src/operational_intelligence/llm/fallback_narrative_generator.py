"""Resilient narrative generator with deterministic fallback."""

from __future__ import annotations

from dataclasses import replace

from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_models import NarrativeResponse, PromptArtifact
from src.operational_intelligence.llm.narrative_protocol import NarrativeGenerator


class FallbackNarrativeGenerator:
    """Try a primary generator and fall back when narrative generation fails."""

    def __init__(
        self,
        primary: NarrativeGenerator,
        fallback: NarrativeGenerator,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return primary narrative or explicit deterministic fallback."""
        try:
            return self._primary.generate(artifact)
        except NarrativeGenerationError as exc:
            fallback_response = self._fallback.generate(artifact)
            return replace(
                fallback_response,
                limitations=(
                    f"{fallback_response.limitations} "
                    f"OpenAI narrative unavailable ({exc}); deterministic fallback applied."
                ),
            )
