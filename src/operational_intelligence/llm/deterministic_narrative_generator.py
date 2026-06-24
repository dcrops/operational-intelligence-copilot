"""Deterministic placeholder narrative generator for boundary validation."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import NarrativeRequest, NarrativeResponse

GENERATOR_TYPE = "deterministic"
LIMITATIONS = (
    "Deterministic narrative placeholder only. LLM narrative generation is not enabled."
)


class DeterministicNarrativeGenerator:
    """Validate the narrative boundary without external services or AI output."""

    def generate(self, request: NarrativeRequest) -> NarrativeResponse:
        """Return the same deterministic narrative for the same request."""
        narrative_parts = [
            "Deterministic narrative assembly (not LLM-generated).",
            f"Question: {request.question}",
            f"Direct answer: {request.direct_answer}",
            f"Executive summary: {request.executive_summary}",
        ]
        if request.operational_assessment:
            narrative_parts.append(f"Operational assessment: {request.operational_assessment}")
        if request.executive_conclusions:
            narrative_parts.append(
                "Executive conclusions: " + "; ".join(request.executive_conclusions)
            )

        key_message = request.executive_summary
        if request.operational_assessment:
            key_message = request.operational_assessment

        return NarrativeResponse(
            executive_narrative="\n".join(narrative_parts),
            key_message=key_message,
            limitations=LIMITATIONS,
            source_sections_used=request.source_sections,
            generator_type=GENERATOR_TYPE,
        )
