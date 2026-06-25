"""Tests for Milestone 11c — OpenAI Adapter & First Narrative Generation."""

from __future__ import annotations

import copy

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    GENERATOR_TYPE as DETERMINISTIC_GENERATOR_TYPE,
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import (
    DEFAULT_OPENAI_MODEL,
    PROVIDER_DETERMINISTIC,
    PROVIDER_OPENAI,
    get_narrative_provider,
)
from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_factory import resolve_narrative_generator
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_TITLES,
    PROMPT_ARTIFACT_VERSION,
)
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    PromptArtifact,
)
from src.operational_intelligence.llm.narrative_briefing import build_limitations_text
from src.operational_intelligence.llm.openai_narrative_generator import (
    GENERATOR_TYPE as OPENAI_GENERATOR_TYPE,
    OpenAINarrativeGenerator,
)
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig
from src.operational_intelligence.llm.openai_response_parser import OpenAINarrativeResponseParser
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.assertions import assert_run_analysis_complete
from tests.support.factories import manufacturing_bundle
from tests.support.fakes import FakeLLMClient
from ui.analysis_service import run_analysis


def _sample_snapshot() -> DeterministicAnalysisSnapshot:
    return DeterministicAnalysisSnapshot(
        question="Which line has the highest defects?",
        direct_answer="Line B has the highest defects.",
        executive_summary="Defect concentration is elevated on Line B.",
        analytical_findings=("Defect variance: Line B exceeds Line A.",),
        operational_assessment="critical: Defect load requires immediate review.",
        executive_conclusions=("Address Line B defect rate.",),
        priority_actions=("Inspect Line B tooling.",),
        transparency_summary=("Temporal filter: none applied.",),
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


def _sample_artifact() -> PromptArtifact:
    request = NarrativeRequestBuilder().build(_sample_snapshot())
    return PromptArtifactBuilder().build(request)


def _sample_llm_response() -> str:
    return (
        "KEY MESSAGE:\n"
        "Line B defect concentration requires executive attention.\n\n"
        "WHY THIS MATTERS:\n"
        "Elevated defects on Line B may affect throughput commitments.\n\n"
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


class TestProviderSelection:
    def test_default_provider_returns_deterministic_generator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.delenv("OIC_NARRATIVE_PROVIDER", raising=False)

        assert get_narrative_provider() == PROVIDER_DETERMINISTIC
        assert isinstance(resolve_narrative_generator(), DeterministicNarrativeGenerator)

    def test_openai_provider_returns_fallback_generator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        assert get_narrative_provider() == PROVIDER_OPENAI
        assert isinstance(resolve_narrative_generator(), FallbackNarrativeGenerator)

    def test_invalid_provider_fails_safe_to_deterministic(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "unknown-provider")

        assert get_narrative_provider() == PROVIDER_DETERMINISTIC


class TestOpenAIPromptFormatter:
    def test_produces_deterministic_messages(self) -> None:
        artifact = _sample_artifact()
        formatter = OpenAIPromptFormatter()

        assert formatter.format(artifact) == formatter.format(artifact)

    def test_includes_evidence_reference_ids(self) -> None:
        messages = OpenAIPromptFormatter().format(_sample_artifact())
        user_message = messages[1]["content"]

        assert "[finding-1]" in user_message
        assert "[direct-answer]" in user_message
        assert "[executive-summary]" in user_message

    def test_excludes_prohibited_internal_content(self) -> None:
        messages = OpenAIPromptFormatter().format(_sample_artifact())
        combined = "\n".join(message["content"] for message in messages).lower()

        assert "routes" not in combined
        assert "openai" not in combined
        assert "temperature" not in combined
        assert "analysis artifacts (json)" not in combined
        assert '"request"' not in combined


class TestOpenAINarrativeResponseParser:
    def test_parses_labelled_sections(self) -> None:
        parsed = OpenAINarrativeResponseParser().parse(_sample_llm_response())

        assert [section.title for section in parsed.sections] == list(ADVISOR_SECTION_TITLES)
        assert parsed.sections[0].content.startswith("Line B defect concentration")
        assert parsed.limitations == "Based only on supplied evidence references."

    def test_raises_for_malformed_output(self) -> None:
        with pytest.raises(NarrativeGenerationError):
            OpenAINarrativeResponseParser().parse("Unstructured response without labels.")


class TestOpenAINarrativeGenerator:
    def test_returns_narrative_response_with_fake_client(self) -> None:
        artifact = _sample_artifact()
        generator = OpenAINarrativeGenerator(
            llm_client=FakeLLMClient(response=_sample_llm_response()),
            config=OpenAIProviderConfig(model="gpt-4.1-mini"),
        )

        response = generator.generate(artifact)

        assert response.generator_type == OPENAI_GENERATOR_TYPE
        assert len(response.sections) == len(ADVISOR_SECTION_TITLES)
        assert response.sections[0].content.startswith("Line B defect concentration")
        assert response.limitations == build_limitations_text(
            generator_type="openai",
            provider_note="Based only on supplied evidence references.",
        )

    def test_records_model_duration_and_artifact_version(self) -> None:
        artifact = _sample_artifact()
        generator = OpenAINarrativeGenerator(
            llm_client=FakeLLMClient(response=_sample_llm_response()),
            config=OpenAIProviderConfig(model=DEFAULT_OPENAI_MODEL),
        )

        response = generator.generate(artifact)

        assert response.model == DEFAULT_OPENAI_MODEL
        assert response.generation_duration_ms is not None
        assert response.generation_duration_ms >= 0
        assert response.artifact_version == PROMPT_ARTIFACT_VERSION


class TestFallbackNarrativeGenerator:
    def test_returns_deterministic_response_when_primary_fails(self) -> None:
        artifact = _sample_artifact()

        class FailingGenerator:
            def generate(self, artifact: PromptArtifact):
                raise NarrativeGenerationError("simulated provider failure")

        response = FallbackNarrativeGenerator(
            primary=FailingGenerator(),
            fallback=DeterministicNarrativeGenerator(),
        ).generate(artifact)

        assert response.generator_type == DETERMINISTIC_GENERATOR_TYPE
        assert "OpenAI narrative unavailable" in response.limitations
        assert "deterministic fallback applied" in response.limitations


class TestOpenAIIntegrationSafety:
    def test_prompt_artifact_unchanged_after_generation(self) -> None:
        artifact = _sample_artifact()
        artifact_before = copy.deepcopy(artifact)

        OpenAINarrativeGenerator(
            llm_client=FakeLLMClient(response=_sample_llm_response()),
            config=OpenAIProviderConfig(model="gpt-4.1-mini"),
        ).generate(artifact)

        assert artifact == artifact_before

    def test_run_analysis_preserves_deterministic_fields_with_openai_provider(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        df, profile = manufacturing_bundle()
        question = "Which production line has the highest defects?"

        baseline = run_analysis(question, df, profile)
        assert baseline.narrative is None

        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        fake_response = _sample_llm_response()

        def _fake_openai_init(self, *args, **kwargs):
            self._model_name = kwargs.get("model_name", DEFAULT_OPENAI_MODEL)
            self._max_retries = kwargs.get("max_retries", 0)
            self._timeout_seconds = kwargs.get("timeout_seconds", 30)

        def _fake_complete(self, messages, temperature=0.0):
            return fake_response

        monkeypatch.setattr(
            "src.operational_intelligence.llm.openai_client.OpenAIClient.__init__",
            _fake_openai_init,
        )
        monkeypatch.setattr(
            "src.operational_intelligence.llm.openai_client.OpenAIClient.complete",
            _fake_complete,
        )

        enabled = run_analysis(question, df, profile)

        assert_run_analysis_complete(enabled)
        assert enabled.narrative is not None
        assert enabled.narrative.generator_type == OPENAI_GENERATOR_TYPE
        assert enabled.request == baseline.request
        assert enabled.routes == baseline.routes
        assert enabled.findings == baseline.findings
        assert enabled.report == baseline.report
        assert enabled.direct_answer == baseline.direct_answer
        assert enabled.deterministic_answer == baseline.deterministic_answer
