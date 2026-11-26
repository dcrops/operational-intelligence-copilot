"""Request-parameter regression tests for OpenAIClient.

These tests do not call the network. They lock gpt-6-luna as the default
OpenAI model, the historical gpt-4.1-mini request, and the gpt-6-luna profile
without changing provider selection or the production retry loop.
"""

from __future__ import annotations

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_config import (
    DEFAULT_OPENAI_MODEL,
    PROVIDER_DETERMINISTIC,
    NarrativeRuntimeConfig,
    get_narrative_provider,
    get_openai_provider_config,
)
from src.operational_intelligence.llm.narrative_factory import (
    resolve_narrative,
    resolve_narrative_generator,
)
from src.operational_intelligence.llm.openai_client import LUNA_CHAT_MODEL, OpenAIClient
from src.operational_intelligence.llm.openai_narrative_generator import (
    OpenAINarrativeGenerator,
)

MESSAGES = [{"role": "user", "content": "Summarise the supplied evidence only."}]


class _Completions:
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[dict] = []
        self._fail = fail

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._fail:
            raise RuntimeError("simulated transport failure")
        message = type("Message", (), {"content": "labelled narrative"})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


class _Client:
    def __init__(self, completions: _Completions) -> None:
        self.completions = completions
        self.chat = type("Chat", (), {"completions": completions})()


def _client(
    monkeypatch: pytest.MonkeyPatch,
    model_name: str,
    *,
    timeout_seconds: int = 30,
    max_retries: int = 0,
    fail: bool = False,
) -> tuple[OpenAIClient, _Completions]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = OpenAIClient(
        model_name=model_name,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
    completions = _Completions(fail=fail)
    client._client = _Client(completions)
    return client, completions


class TestChatRequestParameters:
    def test_luna_is_the_default_openai_model(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_OPENAI_MODEL", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient()
        completions = _Completions()
        client._client = _Client(completions)
        client._max_retries = 0

        client.complete(MESSAGES, temperature=0.0)

        assert DEFAULT_OPENAI_MODEL == "gpt-6-luna"
        assert client._model_name == DEFAULT_OPENAI_MODEL
        assert get_openai_provider_config().model == DEFAULT_OPENAI_MODEL
        call = completions.calls[0]
        assert call["model"] == "gpt-6-luna"
        assert call["reasoning_effort"] == "none"
        assert call["timeout"] == 30
        assert "temperature" not in call
        assert "max_tokens" not in call
        assert "max_completion_tokens" not in call

    def test_mini_preserves_temperature_and_omits_reasoning_effort(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, completions = _client(
            monkeypatch,
            "gpt-4.1-mini",
            timeout_seconds=30,
        )

        assert client.complete(MESSAGES, temperature=0.0) == "labelled narrative"
        assert completions.calls == [
            {
                "model": "gpt-4.1-mini",
                "messages": MESSAGES,
                "timeout": 30,
                "temperature": 0.0,
            }
        ]

    def test_luna_omits_temperature_and_sets_reasoning_effort_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, completions = _client(
            monkeypatch,
            LUNA_CHAT_MODEL,
            timeout_seconds=45,
        )

        client.complete(MESSAGES, temperature=0.0)

        call = completions.calls[0]
        assert call["model"] == "gpt-6-luna"
        assert call["messages"] == MESSAGES
        assert call["timeout"] == 45
        assert call["reasoning_effort"] == "none"
        assert "temperature" not in call
        assert "max_tokens" not in call
        assert "max_completion_tokens" not in call

    def test_other_models_keep_the_historical_parameter_profile(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, completions = _client(monkeypatch, "gpt-4.1")

        client.complete(MESSAGES, temperature=0.0)

        call = completions.calls[0]
        assert call["temperature"] == 0.0
        assert "reasoning_effort" not in call
        assert "max_tokens" not in call

    def test_production_retry_loop_still_retries_transport_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps: list[float] = []
        monkeypatch.setattr("time.sleep", lambda seconds: sleeps.append(seconds))
        client, completions = _client(
            monkeypatch,
            "gpt-4.1-mini",
            max_retries=2,
            fail=True,
        )

        with pytest.raises(RuntimeError, match="failed after 3 attempts"):
            client.complete(MESSAGES, temperature=0.0)

        assert len(completions.calls) == 3
        assert sleeps == [1, 1]
        assert all(call["temperature"] == 0.0 for call in completions.calls)
        assert all("reasoning_effort" not in call for call in completions.calls)


class TestProviderSelectionUnchanged:
    def test_model_environment_does_not_activate_openai(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        monkeypatch.setenv("OIC_OPENAI_MODEL", "gpt-4.1-mini")
        monkeypatch.delenv("OIC_NARRATIVE_PROVIDER", raising=False)

        assert get_narrative_provider() == PROVIDER_DETERMINISTIC
        assert isinstance(resolve_narrative_generator(), DeterministicNarrativeGenerator)

    def test_explicit_model_configuration_remains_available(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_OPENAI_MODEL", raising=False)
        assert get_openai_provider_config().model == DEFAULT_OPENAI_MODEL == "gpt-6-luna"

        monkeypatch.setenv("OIC_OPENAI_MODEL", "gpt-4.1-mini")
        assert get_openai_provider_config().model == "gpt-4.1-mini"

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        explicit = OpenAIClient(model_name="gpt-4.1-mini")
        assert explicit._model_name == "gpt-4.1-mini"

    def test_openai_factory_uses_luna_and_keeps_deterministic_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_OPENAI_MODEL", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        resolution = resolve_narrative(NarrativeRuntimeConfig.openai())

        assert isinstance(resolution.generator, FallbackNarrativeGenerator)
        assert isinstance(resolution.generator._primary, OpenAINarrativeGenerator)
        assert resolution.generator._primary.model_name == DEFAULT_OPENAI_MODEL
        assert isinstance(resolution.generator._fallback, DeterministicNarrativeGenerator)
