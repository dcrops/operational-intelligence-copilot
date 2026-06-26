"""Factory for resolving narrative generators by provider configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

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
    get_openai_provider_config,
)
from src.operational_intelligence.llm.narrative_protocol import NarrativeGenerator
from src.operational_intelligence.llm.narrative_provider_registry import provider_display_name
from src.operational_intelligence.llm.openai_client import OpenAIClient
from src.operational_intelligence.llm.openai_narrative_generator import OpenAINarrativeGenerator

_OPENAI_MISSING_KEY_WARNING = (
    "OpenAI mode selected but no API key was found. "
    "Using deterministic narrative instead."
)
_OPENAI_INIT_FAILED_WARNING = (
    "OpenAI mode selected but provider initialisation failed. "
    "Using deterministic narrative instead."
)


@dataclass(frozen=True)
class NarrativeResolution:
    """Resolved narrative generator plus provider status metadata."""

    generator: NarrativeGenerator
    requested_provider: str
    resolved_provider: str
    warnings: tuple[str, ...]
    fallback_reason: str | None = None


def resolve_narrative(config: NarrativeRuntimeConfig) -> NarrativeResolution:
    """Resolve the narrative generator for explicit runtime configuration."""
    if not config.enabled:
        return NarrativeResolution(
            generator=DeterministicNarrativeGenerator(),
            requested_provider=PROVIDER_DETERMINISTIC,
            resolved_provider=PROVIDER_DETERMINISTIC,
            warnings=(),
        )

    if config.provider != PROVIDER_OPENAI:
        return NarrativeResolution(
            generator=DeterministicNarrativeGenerator(),
            requested_provider=PROVIDER_DETERMINISTIC,
            resolved_provider=PROVIDER_DETERMINISTIC,
            warnings=(),
        )

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return NarrativeResolution(
            generator=DeterministicNarrativeGenerator(),
            requested_provider=PROVIDER_OPENAI,
            resolved_provider=PROVIDER_DETERMINISTIC,
            warnings=(_OPENAI_MISSING_KEY_WARNING,),
            fallback_reason=_OPENAI_MISSING_KEY_WARNING,
        )

    openai_config = get_openai_provider_config()
    try:
        llm_client = OpenAIClient(
            model_name=openai_config.model,
            timeout_seconds=openai_config.timeout_seconds,
        )
    except RuntimeError:
        return NarrativeResolution(
            generator=DeterministicNarrativeGenerator(),
            requested_provider=PROVIDER_OPENAI,
            resolved_provider=PROVIDER_DETERMINISTIC,
            warnings=(_OPENAI_INIT_FAILED_WARNING,),
            fallback_reason=_OPENAI_INIT_FAILED_WARNING,
        )

    return NarrativeResolution(
        generator=FallbackNarrativeGenerator(
            primary=OpenAINarrativeGenerator(llm_client=llm_client, config=openai_config),
            fallback=DeterministicNarrativeGenerator(),
        ),
        requested_provider=PROVIDER_OPENAI,
        resolved_provider=PROVIDER_OPENAI,
        warnings=(),
    )


def resolve_narrative_generator(
    config: NarrativeRuntimeConfig | None = None,
) -> NarrativeGenerator:
    """Return the configured narrative generator (env-backed when config is omitted)."""
    resolved_config = config or NarrativeRuntimeConfig.from_environment()
    return resolve_narrative(resolved_config).generator


def describe_provider_status(config: NarrativeRuntimeConfig) -> tuple[str, str]:
    """Return (status_level, status_message) for sidebar provider status display."""
    resolution = resolve_narrative(config)
    if resolution.resolved_provider == PROVIDER_OPENAI:
        return ("active", provider_display_name(PROVIDER_OPENAI))

    if config.provider == PROVIDER_OPENAI:
        return (
            "warning",
            f"{provider_display_name(PROVIDER_OPENAI)} unavailable\n"
            f"Using {provider_display_name(PROVIDER_DETERMINISTIC)} instead",
        )

    return ("active", provider_display_name(PROVIDER_DETERMINISTIC))
