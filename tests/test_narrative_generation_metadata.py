"""Unit tests for Milestone 12c narrative generation metadata and orchestration."""

from __future__ import annotations

import logging

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
    PROVIDER_DETERMINISTIC,
    PROVIDER_OPENAI,
    NarrativeRuntimeConfig,
)
from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_factory import resolve_narrative
from src.operational_intelligence.llm.narrative_generation import generate_narrative
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
)
from src.operational_intelligence.llm.narrative_provider_registry import (
    build_generation_metadata,
    provider_display_name,
)
from src.operational_intelligence.llm.openai_narrative_generator import (
    GENERATOR_TYPE as OPENAI_GENERATOR_TYPE,
    OpenAINarrativeGenerator,
)
from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.factories import manufacturing_bundle
from tests.support.fakes import FakeLLMClient
from ui.analysis_service import run_analysis
from ui.narrative_presentation import format_generation_method


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


def _sample_artifact():
    request = NarrativeRequestBuilder().build(_sample_snapshot())
    return PromptArtifactBuilder().build(request)


class TestProviderRegistry:
    def test_provider_display_names(self) -> None:
        assert provider_display_name(PROVIDER_DETERMINISTIC) == "Deterministic Engine"
        assert provider_display_name(PROVIDER_OPENAI) == "OpenAI GPT"
        assert provider_display_name(PROVIDER_OPENAI, model="gpt-4.1-mini") == (
            "OpenAI GPT (gpt-4.1-mini)"
        )

    def test_build_generation_metadata_marks_fallback(self) -> None:
        metadata = build_generation_metadata(
            requested_provider=PROVIDER_OPENAI,
            actual_provider=PROVIDER_DETERMINISTIC,
            fallback_reason="Missing API key",
        )
        assert metadata.fallback_used is True
        assert metadata.requested_provider == PROVIDER_OPENAI
        assert metadata.actual_provider == PROVIDER_DETERMINISTIC
        assert metadata.fallback_reason == "Missing API key"


class TestGenerateNarrative:
    def test_deterministic_mode_populates_metadata(self) -> None:
        outcome = generate_narrative(_sample_artifact(), NarrativeRuntimeConfig.deterministic())
        metadata = outcome.response.generation_metadata

        assert metadata is not None
        assert metadata.requested_provider == PROVIDER_DETERMINISTIC
        assert metadata.actual_provider == PROVIDER_DETERMINISTIC
        assert metadata.fallback_used is False
        assert metadata.wall_clock_duration_ms is not None
        assert metadata.wall_clock_duration_ms >= 0
        assert outcome.response.generator_type == DETERMINISTIC_GENERATOR_TYPE
        assert outcome.response.generation_duration_ms == metadata.wall_clock_duration_ms

    def test_missing_api_key_fallback_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        outcome = generate_narrative(_sample_artifact(), NarrativeRuntimeConfig.openai())
        metadata = outcome.response.generation_metadata

        assert metadata is not None
        assert metadata.requested_provider == PROVIDER_OPENAI
        assert metadata.actual_provider == PROVIDER_DETERMINISTIC
        assert metadata.fallback_used is True
        assert metadata.fallback_reason is not None
        assert outcome.warnings

    def test_openai_success_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        def _fake_openai_init(self, *args, **kwargs):
            self._model_name = kwargs.get("model_name", "gpt-4.1-mini")
            self._max_retries = kwargs.get("max_retries", 0)
            self._timeout_seconds = kwargs.get("timeout_seconds", 30)

        def _fake_complete(self, messages, temperature=0.0):
            return (
                "KEY MESSAGE:\nTest message.\n\n"
                "WHY THIS MATTERS:\nBecause it matters.\n\n"
                "WHERE TO INVESTIGATE FIRST:\nStart here.\n\n"
                "POSSIBLE EXPLANATIONS TO CHECK:\nCheck this.\n\n"
                "EXECUTIVE ACTIONS:\nDo this.\n\n"
                "OPERATIONAL INVESTIGATION:\nInvestigate this.\n\n"
                "LIMITATIONS:\nEvidence only."
            )

        monkeypatch.setattr(
            "src.operational_intelligence.llm.openai_client.OpenAIClient.__init__",
            _fake_openai_init,
        )
        monkeypatch.setattr(
            "src.operational_intelligence.llm.openai_client.OpenAIClient.complete",
            _fake_complete,
        )

        outcome = generate_narrative(_sample_artifact(), NarrativeRuntimeConfig.openai())
        metadata = outcome.response.generation_metadata

        assert metadata is not None
        assert metadata.requested_provider == PROVIDER_OPENAI
        assert metadata.actual_provider == OPENAI_GENERATOR_TYPE
        assert metadata.fallback_used is False
        assert metadata.generator_name.startswith("OpenAI GPT")

    def test_runtime_fallback_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        resolution = resolve_narrative(NarrativeRuntimeConfig.openai())

        class FailingOpenAI:
            def generate(self, artifact):
                raise NarrativeGenerationError("provider timeout")

        wrapped = FallbackNarrativeGenerator(
            primary=FailingOpenAI(),
            fallback=DeterministicNarrativeGenerator(),
        )
        monkeypatch.setattr(
            "src.operational_intelligence.llm.narrative_generation.resolve_narrative",
            lambda config: resolution.__class__(
                generator=wrapped,
                requested_provider=resolution.requested_provider,
                resolved_provider=resolution.resolved_provider,
                warnings=resolution.warnings,
                fallback_reason=resolution.fallback_reason,
            ),
        )

        outcome = generate_narrative(_sample_artifact(), NarrativeRuntimeConfig.openai())
        metadata = outcome.response.generation_metadata

        assert metadata is not None
        assert metadata.requested_provider == PROVIDER_OPENAI
        assert metadata.actual_provider == PROVIDER_DETERMINISTIC
        assert metadata.fallback_used is True
        assert metadata.fallback_reason is not None
        assert "provider timeout" in metadata.fallback_reason

    def test_structured_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO)
        generate_narrative(_sample_artifact(), NarrativeRuntimeConfig.deterministic())

        assert any(
            "Narrative generation complete" in record.message
            and "requested_provider=deterministic" in record.message
            and "actual_provider=deterministic" in record.message
            and "wall_clock_duration_ms=" in record.message
            for record in caplog.records
        )


class TestGenerationMethodPresentation:
    def test_fallback_label(self) -> None:
        metadata = build_generation_metadata(
            requested_provider=PROVIDER_OPENAI,
            actual_provider=PROVIDER_DETERMINISTIC,
            fallback_reason="Missing API key",
        )
        status_level, label = format_generation_method(metadata)
        assert status_level == "warning"
        assert label == "Fallback to Deterministic Engine"


class TestRunAnalysisMetadata:
    def test_run_analysis_attaches_generation_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
            narrative_config=NarrativeRuntimeConfig.deterministic(),
        )

        assert result.narrative is not None
        assert result.narrative.generation_metadata is not None
        assert result.narrative.generation_metadata.actual_provider == PROVIDER_DETERMINISTIC
