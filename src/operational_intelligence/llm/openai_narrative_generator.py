"""OpenAI-backed narrative generator."""

from __future__ import annotations

import time

from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_models import NarrativeResponse, PromptArtifact
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig
from src.operational_intelligence.llm.openai_response_parser import OpenAINarrativeResponseParser
from src.operational_intelligence.llm.protocol import LLMClient

GENERATOR_TYPE = "openai"


class OpenAINarrativeGenerator:
    """Generate narrative communication from prompt artifacts via OpenAI."""

    def __init__(
        self,
        llm_client: LLMClient,
        config: OpenAIProviderConfig,
        *,
        prompt_formatter: OpenAIPromptFormatter | None = None,
        response_parser: OpenAINarrativeResponseParser | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._config = config
        self._prompt_formatter = prompt_formatter or OpenAIPromptFormatter()
        self._response_parser = response_parser or OpenAINarrativeResponseParser()

    @property
    def model_name(self) -> str:
        return self._config.model

    def generate(self, artifact: PromptArtifact) -> NarrativeResponse:
        """Return narrative communication for the given prompt artifact."""
        messages = self._prompt_formatter.format(artifact)
        started = time.monotonic()

        try:
            raw_response = self._llm_client.complete(
                messages,
                temperature=self._config.temperature,
            )
        except Exception as exc:
            raise NarrativeGenerationError(
                f"OpenAI narrative generation failed: {exc}"
            ) from exc

        duration_ms = int((time.monotonic() - started) * 1000)

        try:
            parsed = self._response_parser.parse(raw_response)
        except NarrativeGenerationError:
            raise
        except Exception as exc:
            raise NarrativeGenerationError(
                f"Failed to parse OpenAI narrative response: {exc}"
            ) from exc

        return NarrativeResponse(
            executive_narrative=parsed.executive_narrative,
            key_message=parsed.key_message,
            limitations=parsed.limitations,
            source_sections_used=artifact.source_sections,
            generator_type=GENERATOR_TYPE,
            model=self._config.model,
            generation_duration_ms=duration_ms,
            artifact_version=artifact.artifact_version,
        )
