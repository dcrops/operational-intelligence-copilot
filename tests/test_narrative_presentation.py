"""Unit tests for AI-assisted narrative presentation helpers."""

from __future__ import annotations

from src.operational_intelligence.llm.deterministic_narrative_generator import GENERATOR_TYPE
from src.operational_intelligence.llm.narrative_governance import PROMPT_ARTIFACT_VERSION
from src.operational_intelligence.llm.narrative_models import NarrativeResponse
from ui.narrative_presentation import (
    GOVERNANCE_CAPTION,
    NARRATIVE_DISABLED_MESSAGE,
    format_generation_details,
)


def _deterministic_response() -> NarrativeResponse:
    return NarrativeResponse(
        executive_narrative="Deterministic evidence shows Line B has the highest defects.",
        key_message="Line B requires attention.",
        limitations="This narrative was generated using the deterministic narrative generator. AI-generated executive communication is not enabled.",
        source_sections_used=("Direct Answer", "Executive Summary"),
        generator_type=GENERATOR_TYPE,
        model=None,
        generation_duration_ms=None,
        artifact_version=PROMPT_ARTIFACT_VERSION,
    )


def _openai_style_response() -> NarrativeResponse:
    return NarrativeResponse(
        executive_narrative="Line B defect concentration is elevated.",
        key_message="Address Line B defects promptly.",
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
        assert "Artifact version: 1.0" in details

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
        assert "Artifact version: 1.0" in details


class TestGovernanceCopy:
    def test_governance_caption_mentions_deterministic_authority(self) -> None:
        assert "deterministic analysis above" in GOVERNANCE_CAPTION.lower()
        assert "Direct Answer" in GOVERNANCE_CAPTION
        assert "Executive Reasoning" in GOVERNANCE_CAPTION
        assert "System Transparency" in GOVERNANCE_CAPTION

    def test_disabled_message_says_ai_assisted_narrative_not_enabled(self) -> None:
        assert "AI-assisted narrative is not enabled" in NARRATIVE_DISABLED_MESSAGE
        assert "authoritative answer" in NARRATIVE_DISABLED_MESSAGE
