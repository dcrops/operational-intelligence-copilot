"""Convert PromptArtifact into OpenAI-style chat messages."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_LABELS,
    ADVISOR_SECTION_LABEL_LIMITATIONS,
)
from src.operational_intelligence.llm.narrative_models import PromptArtifact

_RESPONSE_SECTION_LABELS = ADVISOR_SECTION_LABELS[:-1]
_LIMITATIONS_LABEL = ADVISOR_SECTION_LABEL_LIMITATIONS


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
            "Treat the executive context and evidence references in the user message "
            "as the complete set of citeable facts."
        )
        if artifact.grounding_constraints.closed_world:
            lines.append("Closed-world grounding applies: do not introduce facts beyond the evidence.")
        if artifact.grounding_constraints.prohibited_behaviours:
            prohibited = ", ".join(artifact.grounding_constraints.prohibited_behaviours)
            lines.append(f"Prohibited behaviours: {prohibited}.")
        lines.append(
            "Respond using exactly these labelled sections:\n"
            + "\n".join(_RESPONSE_SECTION_LABELS + (_LIMITATIONS_LABEL,))
        )
        return "\n".join(lines)

    def _build_user_message(self, artifact: PromptArtifact) -> str:
        context = artifact.executive_context
        lines = [
            f"Question: {context.question}",
            f"Narrative objective: {artifact.narrative_objective}",
            "",
            "Executive context (closed world — use ONLY these business facts):",
            f"Key message: {context.key_message}",
            f"Assessment confidence: {context.assessment_confidence_level} — "
            f"{context.assessment_confidence_rationale}",
            f"Executive assessment: {context.executive_assessment_headline}",
            f"Business summary: {context.business_summary}",
            f"Direct answer: {context.direct_answer_summary}",
            f"Why this matters: {context.why_this_matters}",
        ]

        if context.executive_severity:
            lines.append(f"Executive severity: {context.executive_severity}")
        if context.operational_significance:
            lines.append(f"Operational significance: {context.operational_significance}")
        if context.business_impact:
            lines.append(f"Business impact: {context.business_impact}")
        if context.investigation_strategy:
            lines.append(f"Investigation strategy: {context.investigation_strategy}")
        if context.prioritized_explanations:
            lines.append(f"Prioritized explanations: {context.prioritized_explanations}")
        if context.key_findings:
            lines.append("Business implications:")
            lines.extend(f"- {finding}" for finding in context.key_findings)
        if context.conclusions:
            lines.append("Conclusions:")
            lines.extend(f"- {conclusion}" for conclusion in context.conclusions)
        if context.executive_actions:
            lines.append("Executive actions:")
            lines.extend(f"- {action}" for action in context.executive_actions)
        if context.operational_investigation_actions:
            lines.append("Operational investigation:")
            lines.extend(
                f"- {action}" for action in context.operational_investigation_actions
            )
        if context.investigation_targets:
            lines.append(
                "Investigation targets: " + ", ".join(context.investigation_targets)
            )
        if context.investigation_categories:
            lines.append(
                "Investigation categories: " + "; ".join(context.investigation_categories)
            )
        if context.affected_metrics:
            lines.append("Affected metrics: " + ", ".join(context.affected_metrics))

        lines.extend(
            [
                "",
                "Evidence references (executive language — use ONLY these facts):",
            ]
        )
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
                *_RESPONSE_SECTION_LABELS,
                _LIMITATIONS_LABEL,
            ]
        )
        return "\n".join(lines)
