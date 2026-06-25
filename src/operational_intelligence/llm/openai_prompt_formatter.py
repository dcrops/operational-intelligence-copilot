"""Convert PromptArtifact into OpenAI-style chat messages."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import PromptArtifact

_SECTION_KEY_MESSAGE = "KEY MESSAGE:"
_SECTION_EXECUTIVE_NARRATIVE = "EXECUTIVE NARRATIVE:"
_SECTION_LIMITATIONS = "LIMITATIONS:"


class OpenAIPromptFormatter:
    """Build provider-specific messages from vendor-neutral prompt artifacts."""

    def format(self, artifact: PromptArtifact) -> list[dict[str, str]]:
        """Return deterministic OpenAI-style messages for the given artifact."""
        system_content = self._build_system_message(artifact)
        user_content = self._build_user_message(artifact)
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    def _build_system_message(self, artifact: PromptArtifact) -> str:
        lines = list(artifact.system_instructions)
        lines.append(
            "Treat the evidence references in the user message as the complete set of citeable facts."
        )
        if artifact.grounding_constraints.closed_world:
            lines.append("Closed-world grounding applies: do not introduce facts beyond the evidence.")
        if artifact.grounding_constraints.prohibited_behaviours:
            prohibited = ", ".join(artifact.grounding_constraints.prohibited_behaviours)
            lines.append(f"Prohibited behaviours: {prohibited}.")
        lines.append(
            "Respond using exactly these labelled sections:\n"
            f"{_SECTION_KEY_MESSAGE}\n"
            f"{_SECTION_EXECUTIVE_NARRATIVE}\n"
            f"{_SECTION_LIMITATIONS}"
        )
        return "\n".join(lines)

    def _build_user_message(self, artifact: PromptArtifact) -> str:
        lines = [
            f"Question: {artifact.question}",
            f"Narrative objective: {artifact.narrative_objective}",
            "",
            "Evidence references (closed world — use ONLY these facts):",
        ]
        for reference in artifact.evidence_references:
            lines.append(
                f"[{reference.evidence_id}] ({reference.section}) "
                f"{reference.label}: {reference.content}"
            )

        if artifact.reasoning_trace:
            lines.extend(
                [
                    "",
                    "Reasoning trace (context only — do not treat as new analytical facts):",
                ]
            )
            lines.extend(f"- {line}" for line in artifact.reasoning_trace)

        lines.extend(
            [
                "",
                "Respond using exactly these sections:",
                _SECTION_KEY_MESSAGE,
                _SECTION_EXECUTIVE_NARRATIVE,
                _SECTION_LIMITATIONS,
            ]
        )
        return "\n".join(lines)
