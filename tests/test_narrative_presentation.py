"""Unit tests for AI-assisted narrative presentation helpers."""

from __future__ import annotations

from src.operational_intelligence.llm.deterministic_narrative_generator import GENERATOR_TYPE
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_TITLES,
    PROMPT_ARTIFACT_VERSION,
)
from src.operational_intelligence.llm.narrative_models import (
    AssessmentConfidencePresentation,
    ExecutiveAssessmentBanner,
    NarrativeResponse,
    NarrativeSection,
)
from ui.narrative_presentation import (
    ASSESSMENT_CONFIDENCE_HEADING,
    EXECUTIVE_ASSESSMENT_HEADING,
    GOVERNANCE_CAPTION,
    NARRATIVE_DISABLED_MESSAGE,
    format_assessment_confidence_level,
    format_executive_assessment_banner,
    format_generation_details,
)


def _advisor_sections() -> tuple[NarrativeSection, ...]:
    return tuple(
        NarrativeSection(title=title, content=f"Content for {title}.")
        for title in ADVISOR_SECTION_TITLES
    )


def _deterministic_response() -> NarrativeResponse:
    return NarrativeResponse(
        sections=_advisor_sections(),
        limitations=(
            "This executive narrative is generated from deterministic analytical evidence. "
            "It summarises operational findings and should be interpreted alongside "
            "Executive Reasoning and supporting evidence."
        ),
        source_sections_used=("Direct Answer", "Executive Summary"),
        generator_type=GENERATOR_TYPE,
        model=None,
        generation_duration_ms=None,
        artifact_version=PROMPT_ARTIFACT_VERSION,
    )


def _openai_style_response() -> NarrativeResponse:
    return NarrativeResponse(
        sections=_advisor_sections(),
        limitations="Based only on supplied evidence.",
        source_sections_used=("Direct Answer", "Executive Summary"),
        generator_type="openai",
        model="gpt-4.1-mini",
        generation_duration_ms=842,
        artifact_version=PROMPT_ARTIFACT_VERSION,
    )


class TestFormatGenerationDetails:
    def test_includes_only_non_none_metadata(self) -> None:
        details = format_generation_details(_deterministic_response())

        assert "Generator: deterministic" in details
        assert not any(line.startswith("Model:") for line in details)
        assert not any(line.startswith("Duration:") for line in details)
        assert f"Artifact version: {PROMPT_ARTIFACT_VERSION}" in details

    def test_deterministic_response_omits_model_and_duration_when_none(self) -> None:
        response = _deterministic_response()
        details = format_generation_details(response)

        assert response.model is None
        assert response.generation_duration_ms is None
        assert len(details) == 2

    def test_openai_style_response_includes_model_and_duration_when_present(self) -> None:
        details = format_generation_details(_openai_style_response())

        assert "Generator: openai" in details
        assert "Model: gpt-4.1-mini" in details
        assert "Duration: 842 ms" in details
        assert f"Artifact version: {PROMPT_ARTIFACT_VERSION}" in details


class TestExecutiveBriefingPresentation:
    def test_executive_assessment_banner_includes_heading_and_headline(self) -> None:
        banner = ExecutiveAssessmentBanner(
            level="critical",
            indicator="🔴",
            headline="Multiple critical operational metrics require immediate investigation.",
        )
        formatted = format_executive_assessment_banner(banner)

        assert EXECUTIVE_ASSESSMENT_HEADING in formatted
        assert banner.headline in formatted
        assert "#dc2626" in formatted

    def test_assessment_confidence_level_includes_indicator(self) -> None:
        confidence = AssessmentConfidencePresentation(
            level="High",
            indicator="🟢",
            rationale="Multiple independent analytical signals identified consistent findings.",
        )

        assert "🟢" in format_assessment_confidence_level(confidence)
        assert "High" in format_assessment_confidence_level(confidence)


class TestGovernanceCopy:
    def test_governance_caption_mentions_deterministic_authority(self) -> None:
        assert "deterministic analysis above" in GOVERNANCE_CAPTION.lower()
        assert "Direct Answer" in GOVERNANCE_CAPTION
        assert "Executive Reasoning" in GOVERNANCE_CAPTION
        assert "System Transparency" in GOVERNANCE_CAPTION

    def test_disabled_message_says_ai_assisted_narrative_not_enabled(self) -> None:
        assert "AI-assisted narrative is not enabled" in NARRATIVE_DISABLED_MESSAGE
        assert "authoritative answer" in NARRATIVE_DISABLED_MESSAGE
