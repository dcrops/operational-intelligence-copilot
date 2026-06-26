"""Unit tests for Milestone 12b runtime narrative configuration."""

from __future__ import annotations

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_config import (
    PROVIDER_DETERMINISTIC,
    PROVIDER_OPENAI,
    NarrativeRuntimeConfig,
)
from src.operational_intelligence.llm.narrative_factory import (
    describe_provider_status,
    resolve_narrative,
    resolve_narrative_generator,
)
from ui.analysis_service import run_analysis
from ui.narrative_runtime import (
    NARRATIVE_MODE_DETERMINISTIC,
    NARRATIVE_MODE_OFF,
    NARRATIVE_MODE_OPENAI,
    narrative_mode_from_environment,
    narrative_mode_to_config,
)
from ui.narrative_service import maybe_generate_narrative
from tests.support.factories import manufacturing_bundle


class TestNarrativeRuntimeConfig:
    def test_from_environment_defaults_to_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        assert NarrativeRuntimeConfig.from_environment() == NarrativeRuntimeConfig.disabled()

    def test_from_environment_maps_deterministic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "deterministic")
        assert NarrativeRuntimeConfig.from_environment() == NarrativeRuntimeConfig.deterministic()

    def test_from_environment_maps_openai(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "1")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "openai")
        assert NarrativeRuntimeConfig.from_environment() == NarrativeRuntimeConfig.openai()


class TestNarrativeModeMapping:
    def test_mode_to_config(self) -> None:
        assert narrative_mode_to_config(NARRATIVE_MODE_OFF) == NarrativeRuntimeConfig.disabled()
        assert narrative_mode_to_config(NARRATIVE_MODE_DETERMINISTIC) == (
            NarrativeRuntimeConfig.deterministic()
        )
        assert narrative_mode_to_config(NARRATIVE_MODE_OPENAI) == NarrativeRuntimeConfig.openai()

    def test_environment_to_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        assert narrative_mode_from_environment() == NARRATIVE_MODE_DETERMINISTIC

        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "openai")
        assert narrative_mode_from_environment() == NARRATIVE_MODE_OPENAI


class TestNarrativeResolution:
    def test_disabled_config_returns_deterministic_generator(self) -> None:
        resolution = resolve_narrative(NarrativeRuntimeConfig.disabled())
        assert isinstance(resolution.generator, DeterministicNarrativeGenerator)
        assert resolution.resolved_provider == PROVIDER_DETERMINISTIC
        assert resolution.warnings == ()

    def test_openai_without_api_key_falls_back_with_warning(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        resolution = resolve_narrative(NarrativeRuntimeConfig.openai())
        assert isinstance(resolution.generator, DeterministicNarrativeGenerator)
        assert resolution.requested_provider == PROVIDER_OPENAI
        assert resolution.resolved_provider == PROVIDER_DETERMINISTIC
        assert len(resolution.warnings) == 1

    def test_openai_with_api_key_returns_fallback_generator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        resolution = resolve_narrative(NarrativeRuntimeConfig.openai())
        assert isinstance(resolution.generator, FallbackNarrativeGenerator)
        assert resolution.resolved_provider == PROVIDER_OPENAI

    def test_resolve_narrative_generator_uses_explicit_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        generator = resolve_narrative_generator(NarrativeRuntimeConfig.deterministic())
        assert isinstance(generator, DeterministicNarrativeGenerator)


class TestProviderStatus:
    def test_disabled_status(self) -> None:
        level, message = describe_provider_status(NarrativeRuntimeConfig.disabled())
        assert level == "active"
        assert message == "Deterministic Engine"

    def test_deterministic_active_status(self) -> None:
        level, message = describe_provider_status(NarrativeRuntimeConfig.deterministic())
        assert level == "active"
        assert message == "Deterministic Engine"

    def test_openai_unavailable_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        level, message = describe_provider_status(NarrativeRuntimeConfig.openai())
        assert level == "warning"
        assert "OpenAI GPT unavailable" in message
        assert "Deterministic Engine" in message


class TestExplicitConfigInService:
    def test_disabled_config_skips_narrative_despite_enabled_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
            narrative_config=NarrativeRuntimeConfig.disabled(),
        )
        assert result.narrative is None

    def test_maybe_generate_narrative_honours_explicit_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
            narrative_config=NarrativeRuntimeConfig.disabled(),
        )
        narrative, warnings = maybe_generate_narrative(
            result,
            config=NarrativeRuntimeConfig.disabled(),
        )
        assert narrative is None
        assert warnings == ()
