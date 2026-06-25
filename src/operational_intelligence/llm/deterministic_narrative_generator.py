"""Deterministic narrative generator for boundary validation and graceful fallback."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import PromptArtifact, NarrativeResponse

GENERATOR_TYPE = "deterministic"
LIMITATIONS = (
    "This narrative was generated using the deterministic narrative generator. "
    "AI-generated executive communication is not enabled."
)


def _normalize_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if cleaned.endswith("."):
        return cleaned
    return f"{cleaned}."


def _assessment_prose(operational_assessment: str) -> str:
    if ": " in operational_assessment:
        level, rationale = operational_assessment.split(": ", 1)
        level_text = level.replace("_", " ")
        return (
            f"The situation is assessed as {level_text}. "
            f"{_normalize_sentence(rationale)}"
        )
    return _normalize_sentence(operational_assessment)


def _finding_prose(analytical_findings: tuple[str, ...]) -> str:
    sentences: list[str] = []
    for finding in analytical_findings:
        if ": " in finding:
            _, description = finding.split(": ", 1)
            sentences.append(_normalize_sentence(description))
        else:
            sentences.append(_normalize_sentence(finding))
    return " ".join(sentences)


def _conclusions_prose(executive_conclusions: tuple[str, ...]) -> str:
    if len(executive_conclusions) == 1:
        return f"A key conclusion is that {executive_conclusions[0].rstrip('.')}."
    joined = "; ".join(conclusion.rstrip(".") for conclusion in executive_conclusions)
    return f"The analysis concludes that {joined}."


def _priority_actions_prose(priority_actions: tuple[str, ...]) -> str:
    if len(priority_actions) == 1:
        action = priority_actions[0].rstrip(".")
        return f"The recommended priority action is {action}."
    joined = "; ".join(action.rstrip(".") for action in priority_actions)
    return f"Recommended priority actions include: {joined}."


def _build_key_message(artifact: PromptArtifact) -> str:
    if artifact.operational_assessment and ": " in artifact.operational_assessment:
        _, rationale = artifact.operational_assessment.split(": ", 1)
        return _normalize_sentence(rationale)
    if artifact.executive_summary:
        return _normalize_sentence(artifact.executive_summary)
    return _normalize_sentence(artifact.direct_answer)


def _build_executive_narrative(artifact: PromptArtifact) -> str:
    paragraphs: list[str] = []

    if artifact.executive_summary:
        paragraphs.append(_normalize_sentence(artifact.executive_summary))

    direct_answer = artifact.direct_answer.strip()
    summary = artifact.executive_summary.strip().lower()
    if direct_answer and direct_answer.lower() not in summary and summary not in direct_answer.lower():
        paragraphs.append(_normalize_sentence(direct_answer))

    finding_text = _finding_prose(artifact.analytical_findings)
    if finding_text:
        paragraphs.append(finding_text)

    if artifact.operational_assessment:
        paragraphs.append(_assessment_prose(artifact.operational_assessment))

    if artifact.executive_conclusions:
        paragraphs.append(_conclusions_prose(artifact.executive_conclusions))

    if artifact.priority_actions:
        paragraphs.append(_priority_actions_prose(artifact.priority_actions))

    return "\n\n".join(paragraphs)


class DeterministicNarrativeGenerator:
    """Produce executive-style narrative prose from deterministic prompt artifacts."""

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return the same deterministic narrative for the same artifact."""
        return NarrativeResponse(
            executive_narrative=_build_executive_narrative(artifact),
            key_message=_build_key_message(artifact),
            limitations=LIMITATIONS,
            source_sections_used=artifact.source_sections,
            generator_type=GENERATOR_TYPE,
            model=None,
            generation_duration_ms=None,
            artifact_version=artifact.artifact_version,
        )
