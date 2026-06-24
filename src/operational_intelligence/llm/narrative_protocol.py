"""Protocol for AI narrative generation."""

from __future__ import annotations

from typing import Protocol

from src.operational_intelligence.llm.narrative_models import NarrativeRequest, NarrativeResponse


class NarrativeGenerator(Protocol):
    """Generate narrative communication from deterministic analysis snapshots."""

    def generate(self, request: NarrativeRequest) -> NarrativeResponse:
        """Return narrative communication for the given deterministic request."""
        ...
