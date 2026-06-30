"""Tests for Milestone 11e — AI Executive Advisor."""

from __future__ import annotations

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_LABELS,
    ADVISOR_SECTION_LABEL_LIMITATIONS,
    ADVISOR_SECTION_TITLES,
    DEFAULT_NARRATIVE_OBJECTIVE,
    OBJECTIVE_EXECUTIVE_ADVISOR,
    PROMPT_ARTIFACT_VERSION,
    PROHIBITED_BEHAVIOURS,
    SYSTEM_INSTRUCTIONS,
)
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    NarrativeSection,
)
from src.operational_intelligence.llm.narrative_briefing import build_limitations_text
from src.operational_intelligence.llm.openai_narrative_generator import OpenAINarrativeGenerator
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig
from src.operational_intelligence.llm.openai_response_parser import OpenAINarrativeResponseParser
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.fakes import FakeLLMClient


def _sample_snapshot(*, transparency_summary: tuple[str, ...] | None = None) -> DeterministicAnalysisSnapshot:
    return DeterministicAnalysisSnapshot(
        question="Which line has the highest defects?",
        direct_answer="Line B has the highest defects.",
        executive_summary="Defect concentration is elevated on Line B.",
        analytical_findings=("Defect variance: Line B exceeds Line A.",),
        operational_assessment="critical: Defect load requires immediate review.",
        executive_conclusions=("Address Line B defect rate.",),
        priority_actions=("Inspect Line B tooling.",),
        transparency_summary=transparency_summary
        or ("Temporal filter: none applied.", "Dimension: production_line"),
        reasoning_trace=("Theme 1: Defect concentration",),
        source_sections=(
            "Direct Answer",
            "Executive Summary",
            "Analytical Findings",
            "Operational Assessment",
            "Executive Conclusions",
            "Priority Actions",
            "System Transparency",
        ),
    )


def _sample_artifact(*, transparency_summary: tuple[str, ...] | None = None):
    request = NarrativeRequestBuilder().build(
        _sample_snapshot(transparency_summary=transparency_summary)
    )
    return PromptArtifactBuilder().build(request)


def _sample_advisor_llm_response() -> str:
    return (
        "KEY MESSAGE:\n"
        "Line B defect concentration requires executive attention.\n\n"
        "WHY THIS MATTERS:\n"
        "Elevated defects on Line B may affect throughput and quality commitments.\n\n"
        "WHERE TO INVESTIGATE FIRST:\n"
        "Begin by comparing defect rates across production lines.\n\n"
        "POSSIBLE EXPLANATIONS TO CHECK:\n"
        "Possible causes to check include tooling wear or a recent process change.\n\n"
        "EXECUTIVE ACTIONS:\n"
        "Validate source data before escalation.\n\n"
        "OPERATIONAL INVESTIGATION:\n"
        "Inspect Line B tooling and validate recent maintenance records.\n\n"
        "LIMITATIONS:\n"
        "Based only on supplied evidence references."
    )


class TestGovernanceAndPromptContract:
    def test_default_objective_is_executive_advisor(self) -> None:
        artifact = _sample_artifact()
        assert artifact.narrative_objective == OBJECTIVE_EXECUTIVE_ADVISOR
        assert DEFAULT_NARRATIVE_OBJECTIVE == OBJECTIVE_EXECUTIVE_ADVISOR

    def test_artifact_version_is_1_2(self) -> None:
        assert _sample_artifact().artifact_version == "1.2"
        assert PROMPT_ARTIFACT_VERSION == "1.2"

    def test_system_instructions_include_plain_language_and_hypothesis_rules(self) -> None:
        combined = " ".join(SYSTEM_INSTRUCTIONS).lower()
        assert "plain business language" in combined
        assert "statistical jargon" in combined
        assert "hypotheses" in combined

    def test_prohibited_behaviours_include_unsupported_causes_and_jargon(self) -> None:
        assert "confirm_unsupported_causes" in PROHIBITED_BEHAVIOURS
        assert "use_statistical_jargon_in_advisor_text" in PROHIBITED_BEHAVIOURS

    def test_prompt_formatter_requests_advisor_section_labels(self) -> None:
        messages = OpenAIPromptFormatter().format(_sample_artifact())
        combined = "\n".join(message["content"] for message in messages)

        for label in ADVISOR_SECTION_LABELS:
            assert label in combined

    def test_prompt_formatter_includes_closed_world_evidence(self) -> None:
        user_message = OpenAIPromptFormatter().format(_sample_artifact())[1]["content"]
        assert "closed world" in user_message.lower()
        assert "Executive context" in user_message
        assert "[finding-1]" in user_message


class TestOpenAINarrativeResponseParser:
    def test_parses_ordered_advisor_sections(self) -> None:
        parsed = OpenAINarrativeResponseParser().parse(_sample_advisor_llm_response())

        assert [section.title for section in parsed.sections] == list(ADVISOR_SECTION_TITLES)
        assert parsed.sections[0].title == "Key Message"
        assert "executive attention" in parsed.sections[0].content
        assert parsed.limitations == "Based only on supplied evidence references."

    def test_raises_for_malformed_output(self) -> None:
        with pytest.raises(NarrativeGenerationError):
            OpenAINarrativeResponseParser().parse("Unstructured response without labels.")

    def test_raises_when_required_section_missing(self) -> None:
        incomplete = (
            "KEY MESSAGE:\n"
            "A concise message.\n\n"
            "LIMITATIONS:\n"
            "None."
        )
        with pytest.raises(NarrativeGenerationError):
            OpenAINarrativeResponseParser().parse(incomplete)


class TestOpenAINarrativeGeneratorMapping:
    def test_maps_parsed_sections_to_narrative_response(self) -> None:
        response = OpenAINarrativeGenerator(
            llm_client=FakeLLMClient(response=_sample_advisor_llm_response()),
            config=OpenAIProviderConfig(model="gpt-4.1-mini"),
        ).generate(_sample_artifact())

        assert len(response.sections) == len(ADVISOR_SECTION_TITLES)
        assert all(isinstance(section, NarrativeSection) for section in response.sections)
        assert response.generator_type == "openai"
        assert response.limitations == build_limitations_text(
            generator_type="openai",
            provider_note="Based only on supplied evidence references.",
        )


class TestDeterministicAdvisorGeneration:
    def test_produces_six_ordered_advisor_sections(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        assert [section.title for section in response.sections] == list(ADVISOR_SECTION_TITLES)
        assert response.executive_assessment is not None
        assert response.assessment_confidence is not None

    def test_investigation_guidance_references_available_dimensions(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())
        investigate = next(
            section.content
            for section in response.sections
            if section.title == "Where To Investigate First"
        )

        assert "production line" in investigate.lower()
        assert "z-score" not in investigate.lower()

    def test_executive_actions_reference_available_dimensions(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())
        executive_actions = next(
            section.content
            for section in response.sections
            if section.title == "Executive Actions"
        )

        assert "inspect line b tooling" in executive_actions.lower()
        assert "Inspect Line B tooling" in executive_actions or any(
            "Inspect Line B tooling" in section.content
            for section in response.sections
            if section.title == "Operational Investigation"
        )

    def test_possible_explanations_use_hypothesis_language(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())
        explanations = next(
            section.content
            for section in response.sections
            if section.title == "Possible Explanations To Check"
        )

        assert "plausible explanations" in explanations.lower()
        assert "hypothesis" in explanations.lower()

    def test_does_not_invent_dimensions_when_absent(self) -> None:
        artifact = _sample_artifact(transparency_summary=("Temporal filter: none applied.",))
        investigate = next(
            section.content
            for section in DeterministicNarrativeGenerator().generate(artifact).sections
            if section.title == "Where To Investigate First"
        )

        assert "school" not in investigate.lower()
        assert "department" not in investigate.lower()


class TestParserFailureFallback:
    def test_fallback_returns_deterministic_advisor_sections(self) -> None:
        class FailingGenerator:
            def generate(self, artifact):
                raise NarrativeGenerationError("simulated parser failure")

        response = FallbackNarrativeGenerator(
            primary=FailingGenerator(),
            fallback=DeterministicNarrativeGenerator(),
        ).generate(_sample_artifact())

        assert [section.title for section in response.sections] == list(ADVISOR_SECTION_TITLES)
        assert "deterministic fallback applied" in response.limitations.lower()


class TestSectionRenderingStructure:
    def test_narrative_response_sections_are_iterable_for_ui(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        rendered = [(section.title, section.content) for section in response.sections]
        assert len(rendered) == 6
        assert all(title and content for title, content in rendered)
