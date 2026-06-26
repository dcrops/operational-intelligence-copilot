"""Stable narrative provider IDs, display names, and generation metadata."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_config import PROVIDER_DETERMINISTIC, PROVIDER_OPENAI
from src.operational_intelligence.llm.narrative_models import NarrativeGenerationMetadata

_PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    PROVIDER_DETERMINISTIC: "Deterministic Engine",
    PROVIDER_OPENAI: "OpenAI GPT",
}

_RUNTIME_FALLBACK_REASON = (
    "OpenAI narrative generation failed; deterministic fallback applied."
)


def provider_display_name(provider_id: str, *, model: str | None = None) -> str:
    """Return a user-facing provider label for a stable provider ID."""
    base = _PROVIDER_DISPLAY_NAMES.get(provider_id, provider_id.title())
    if provider_id == PROVIDER_OPENAI and model:
        return f"{base} ({model})"
    return base


def build_generation_metadata(
    *,
    requested_provider: str,
    actual_provider: str,
    model: str | None = None,
    provider_version: str | None = None,
    wall_clock_duration_ms: int | None = None,
    fallback_reason: str | None = None,
) -> NarrativeGenerationMetadata:
    """Build authoritative generation metadata from resolved provider facts."""
    fallback_used = requested_provider != actual_provider
    resolved_reason = fallback_reason
    if fallback_used and not resolved_reason:
        resolved_reason = _RUNTIME_FALLBACK_REASON

    return NarrativeGenerationMetadata(
        generator_name=provider_display_name(actual_provider, model=model),
        requested_provider=requested_provider,
        actual_provider=actual_provider,
        fallback_used=fallback_used,
        fallback_reason=resolved_reason if fallback_used else None,
        wall_clock_duration_ms=wall_clock_duration_ms,
        model=model,
        provider_version=provider_version,
    )
