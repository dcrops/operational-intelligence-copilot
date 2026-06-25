"""Factory for resolving narrative generators by provider configuration."""

from __future__ import annotations

import os

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_config import (
    PROVIDER_OPENAI,
    get_narrative_provider,
    get_openai_provider_config,
)
from src.operational_intelligence.llm.narrative_protocol import NarrativeGenerator
from src.operational_intelligence.llm.openai_client import OpenAIClient
from src.operational_intelligence.llm.openai_narrative_generator import OpenAINarrativeGenerator


def resolve_narrative_generator() -> NarrativeGenerator:
    """Return the configured narrative generator for the current environment."""
    provider = get_narrative_provider()
    if provider != PROVIDER_OPENAI:
        return DeterministicNarrativeGenerator()

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return DeterministicNarrativeGenerator()

    config = get_openai_provider_config()
    try:
        llm_client = OpenAIClient(
            model_name=config.model,
            timeout_seconds=config.timeout_seconds,
        )
    except RuntimeError:
        return DeterministicNarrativeGenerator()

    return FallbackNarrativeGenerator(
        primary=OpenAINarrativeGenerator(llm_client=llm_client, config=config),
        fallback=DeterministicNarrativeGenerator(),
    )
