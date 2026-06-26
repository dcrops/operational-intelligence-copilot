"""Unit tests for executive narrative presentation helpers."""

from __future__ import annotations

from src.operational_intelligence.llm.deterministic_narrative_generator import GENERATOR_TYPE
from src.operational_intelligence.llm.narrative_config import PROVIDER_DETERMINISTIC, PROVIDER_OPENAI
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_TITLES,
    PROMPT_ARTIFACT_VERSION,
)
from src.operational_intelligence.llm.narrative_models import (
    AssessmentConfidencePresentation,
    ExecutiveAssessmentBanner,
    NarrativeGenerationMetadata,
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
    format_generated_by_secondary_metadata,
    format_generation_details,
    format_generation_method,
)


def _advisor_sections() -> tuple[NarrativeSection, ...]:
    return tuple(
        NarrativeSection(title=title, content=f"Content for {title}.")
        for title in ADVISOR_SECTION_TITLES
    )


def _deterministic_metadata() -> NarrativeGenerationMetadata:
    return NarrativeGenerationMetadata(
        generator_name="Deterministic Engine",
        requested_provider=PROVIDER_DETERMINISTIC,
        actual_provider=PROVIDER_DETERMINISTIC,
        fallback_used=False,
        wall_clock_duration_ms=12,
        provider_version=PROMPT_ARTIFACT_VERSION,
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
        generation_duration_ms=12,
        artifact_version=PROMPT_ARTIFACT_VERSION,
        generation_metadata=_deterministic_metadata(),
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
        generation_metadata=NarrativeGenerationMetadata(
            generator_name="OpenAI GPT (gpt-4.1-mini)",
            requested_provider=PROVIDER_OPENAI,
            actual_provider=PROVIDER_OPENAI,
            fallback_used=False,
            wall_clock_duration_ms=842,
            model="gpt-4.1-mini",
            provider_version=PROMPT_ARTIFACT_VERSION,
        ),
    )


class TestFormatGenerationDetails:
    def test_metadata_first_details(self) -> None:
        details = format_generation_details(_deterministic_response())

        assert "Requested provider: deterministic" in details
        assert "Actual provider: deterministic" in details
        assert "Generator: Deterministic Engine" in details
        assert "Generation Time: 12 ms" in details

    def test_legacy_fallback_when_metadata_missing(self) -> None:
        response = NarrativeResponse(
            sections=_advisor_sections(),
            limitations="Legacy response.",
            source_sections_used=("Direct Answer",),
            generator_type=GENERATOR_TYPE,
            artifact_version=PROMPT_ARTIFACT_VERSION,
        )
        details = format_generation_details(response)

        assert "Generator: deterministic" in details
        assert f"Provider version: {PROMPT_ARTIFACT_VERSION}" in details

    def test_openai_style_response_includes_model_and_duration_when_present(self) -> None:
        details = format_generation_details(_openai_style_response())

        assert "Actual provider: openai" in details
        assert "Model: gpt-4.1-mini" in details
        assert "Generation Time: 842 ms" in details


class TestFormatGeneratedBySecondaryMetadata:
    def test_includes_model_and_generation_time_when_present(self) -> None:
        lines = format_generated_by_secondary_metadata(
            NarrativeGenerationMetadata(
                generator_name="OpenAI GPT (gpt-4.1-mini)",
                requested_provider=PROVIDER_OPENAI,
                actual_provider=PROVIDER_OPENAI,
                fallback_used=False,
                wall_clock_duration_ms=842,
                model="gpt-4.1-mini",
            )
        )

        assert lines == ("Model: gpt-4.1-mini", "Generation Time: 842 ms")


class TestFormatGenerationMethod:
    def test_active_deterministic_label(self) -> None:
        status_level, label = format_generation_method(_deterministic_metadata())
        assert status_level == "active"
        assert label == "Deterministic Engine"

    def test_fallback_label(self) -> None:
        metadata = NarrativeGenerationMetadata(
            generator_name="Deterministic Engine",
            requested_provider=PROVIDER_OPENAI,
            actual_provider=PROVIDER_DETERMINISTIC,
            fallback_used=True,
            fallback_reason="Missing API key",
        )
        status_level, label = format_generation_method(metadata)
        assert status_level == "warning"
        assert label == "Fallback to Deterministic Engine"


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

    def test_disabled_message_mentions_authoritative_answer(self) -> None:
        assert "Executive summary is unavailable" in NARRATIVE_DISABLED_MESSAGE
        assert "authoritative answer" in NARRATIVE_DISABLED_MESSAGE
