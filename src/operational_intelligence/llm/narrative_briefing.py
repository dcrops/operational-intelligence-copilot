"""Assemble executive narrative sections and presentation metadata."""

from __future__ import annotations

from dataclasses import replace

from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_EXECUTIVE_ACTIONS,
    ADVISOR_SECTION_KEY_MESSAGE,
    ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
    ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
    ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
    ADVISOR_SECTION_WHY_THIS_MATTERS,
)
from src.operational_intelligence.llm.narrative_models import (
    AssessmentConfidencePresentation,
    ExecutiveAssessmentBanner,
    ExecutiveContext,
    NarrativeGenerationMetadata,
    NarrativeResponse,
    NarrativeSection,
)

_CONFIDENCE_INDICATORS = {
    "High": "🟢",
    "Medium": "🟡",
    "Low": "🟡",
}

ARCHITECTURE_LIMITATIONS = (
    "This executive narrative is generated from deterministic analytical evidence. "
    "It summarises operational findings and should be interpreted alongside "
    "Executive Reasoning and supporting evidence."
)

DETERMINISTIC_PROVIDER_NOTE = (
    "This briefing was assembled deterministically from the same evidence shown above."
)


def _normalize_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if cleaned.endswith("."):
        return cleaned
    return f"{cleaned}."


def _format_action_section(actions: tuple[str, ...]) -> str:
    if not actions:
        return "No specific actions identified from the available evidence."
    return "\n".join(f"- {action}" for action in actions)


def build_limitations_text(*, generator_type: str, provider_note: str | None = None) -> str:
    """Return user-facing limitations copy for the narrative provider."""
    limitations = ARCHITECTURE_LIMITATIONS
    if generator_type == "deterministic":
        limitations = f"{limitations} {DETERMINISTIC_PROVIDER_NOTE}"
    if provider_note:
        limitations = f"{limitations} {provider_note}"
    return limitations


def build_executive_assessment_banner(context: ExecutiveContext) -> ExecutiveAssessmentBanner:
    """Build deterministic executive assessment banner metadata."""
    return ExecutiveAssessmentBanner(
        level=context.executive_assessment_level,
        indicator=context.executive_assessment_indicator,
        headline=context.executive_assessment_headline,
    )


def build_assessment_confidence_presentation(
    context: ExecutiveContext,
) -> AssessmentConfidencePresentation:
    """Build structured assessment confidence metadata."""
    return AssessmentConfidencePresentation(
        level=context.assessment_confidence_level,
        indicator=_CONFIDENCE_INDICATORS.get(context.assessment_confidence_level, ""),
        rationale=context.assessment_confidence_rationale,
    )


def build_advisor_sections(context: ExecutiveContext) -> tuple[NarrativeSection, ...]:
    """Build ordered advisor sections from executive context."""
    return (
        NarrativeSection(
            title=ADVISOR_SECTION_KEY_MESSAGE,
            content=_normalize_sentence(context.key_message),
        ),
        NarrativeSection(
            title=ADVISOR_SECTION_WHY_THIS_MATTERS,
            content=_normalize_sentence(context.why_this_matters),
        ),
        NarrativeSection(
            title=ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
            content=_normalize_sentence(context.investigation_strategy),
        ),
        NarrativeSection(
            title=ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
            content=_normalize_sentence(context.prioritized_explanations),
        ),
        NarrativeSection(
            title=ADVISOR_SECTION_EXECUTIVE_ACTIONS,
            content=_format_action_section(context.executive_actions),
        ),
        NarrativeSection(
            title=ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
            content=_format_action_section(context.operational_investigation_actions),
        ),
    )


def build_narrative_response(
    context: ExecutiveContext,
    *,
    generator_type: str,
    source_sections_used: tuple[str, ...],
    limitations: str | None = None,
    model: str | None = None,
    generation_duration_ms: int | None = None,
    artifact_version: str | None = None,
    sections: tuple[NarrativeSection, ...] | None = None,
) -> NarrativeResponse:
    """Build a complete narrative response with presentation metadata."""
    return NarrativeResponse(
        sections=sections or build_advisor_sections(context),
        limitations=limitations or build_limitations_text(generator_type=generator_type),
        source_sections_used=source_sections_used,
        generator_type=generator_type,
        executive_assessment=build_executive_assessment_banner(context),
        assessment_confidence=build_assessment_confidence_presentation(context),
        model=model,
        generation_duration_ms=generation_duration_ms,
        artifact_version=artifact_version,
    )


def attach_generation_metadata(
    response: NarrativeResponse,
    metadata: NarrativeGenerationMetadata,
) -> NarrativeResponse:
    """Attach metadata and synchronise legacy response fields for backward compatibility."""
    return replace(
        response,
        generator_type=metadata.actual_provider,
        model=metadata.model if metadata.model is not None else response.model,
        generation_duration_ms=metadata.wall_clock_duration_ms,
        artifact_version=(
            metadata.provider_version
            if metadata.provider_version is not None
            else response.artifact_version
        ),
        generation_metadata=metadata,
    )
