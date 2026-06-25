"""Deterministic placeholder narrative generator for boundary validation."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import NarrativeResponse, PromptArtifact

GENERATOR_TYPE = "deterministic"
LIMITATIONS = (
    "Deterministic narrative placeholder only. LLM narrative generation is not enabled."
)


class DeterministicNarrativeGenerator:
    """Validate the narrative boundary without external services or AI output."""

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return the same deterministic narrative for the same artifact."""
        narrative_parts = [
            "Deterministic narrative assembly (not LLM-generated).",
            f"Objective: {artifact.narrative_objective}",
            f"Question: {artifact.question}",
            f"Direct answer: {artifact.direct_answer}",
            f"Executive summary: {artifact.executive_summary}",
        ]
        if artifact.operational_assessment:
            narrative_parts.append(
                f"Operational assessment: {artifact.operational_assessment}"
            )
        if artifact.executive_conclusions:
            narrative_parts.append(
                "Executive conclusions: " + "; ".join(artifact.executive_conclusions)
            )
        if artifact.evidence_references:
            narrative_parts.append(
                "Evidence references: "
                + ", ".join(ref.evidence_id for ref in artifact.evidence_references)
            )

        key_message = artifact.executive_summary
        if artifact.operational_assessment:
            key_message = artifact.operational_assessment

        return NarrativeResponse(
            executive_narrative="\n".join(narrative_parts),
            key_message=key_message,
            limitations=LIMITATIONS,
            source_sections_used=artifact.source_sections,
            generator_type=GENERATOR_TYPE,
            model=None,
            generation_duration_ms=None,
            artifact_version=artifact.artifact_version,
        )
