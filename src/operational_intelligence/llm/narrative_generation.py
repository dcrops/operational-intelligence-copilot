"""Orchestration for narrative generation with metadata enrichment and logging."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

from src.operational_intelligence.llm.narrative_briefing import attach_generation_metadata
from src.operational_intelligence.llm.narrative_config import (
    PROVIDER_DETERMINISTIC,
    PROVIDER_OPENAI,
    NarrativeRuntimeConfig,
)
from src.operational_intelligence.llm.narrative_factory import NarrativeResolution, resolve_narrative
from src.operational_intelligence.llm.narrative_models import (
    NarrativeGenerationMetadata,
    NarrativeResponse,
    PromptArtifact,
)
from src.operational_intelligence.llm.narrative_provider_registry import build_generation_metadata

logger = logging.getLogger(__name__)

_RUNTIME_FALLBACK_PATTERN = re.compile(
    r"OpenAI narrative unavailable \((?P<reason>.+?)\); deterministic fallback applied\."
)


@dataclass(frozen=True)
class NarrativeGenerationOutcome:
    """Narrative response enriched with authoritative generation metadata."""

    response: NarrativeResponse
    warnings: tuple[str, ...]


def _runtime_fallback_reason_from_limitations(limitations: str) -> str | None:
    match = _RUNTIME_FALLBACK_PATTERN.search(limitations)
    if match is None:
        return None
    return f"OpenAI narrative generation failed: {match.group('reason')}"


def _resolve_fallback_reason(
    resolution: NarrativeResolution,
    response: NarrativeResponse,
) -> str | None:
    if resolution.fallback_reason is not None:
        return resolution.fallback_reason

    if (
        resolution.requested_provider == PROVIDER_OPENAI
        and response.generator_type == PROVIDER_DETERMINISTIC
        and resolution.resolved_provider == PROVIDER_OPENAI
    ):
        return _runtime_fallback_reason_from_limitations(response.limitations)

    return None


def generate_narrative(
    artifact: PromptArtifact,
    config: NarrativeRuntimeConfig,
) -> NarrativeGenerationOutcome:
    """Resolve provider, generate narrative, enrich metadata, and log the outcome."""
    resolution = resolve_narrative(config)

    started = time.monotonic()
    response = resolution.generator.generate(artifact)
    wall_clock_duration_ms = int((time.monotonic() - started) * 1000)

    fallback_reason = _resolve_fallback_reason(resolution, response)
    metadata = build_generation_metadata(
        requested_provider=resolution.requested_provider,
        actual_provider=response.generator_type,
        model=response.model,
        provider_version=response.artifact_version,
        wall_clock_duration_ms=wall_clock_duration_ms,
        fallback_reason=fallback_reason,
    )
    enriched = attach_generation_metadata(response, metadata)
    _log_narrative_generation(config, metadata)
    return NarrativeGenerationOutcome(response=enriched, warnings=resolution.warnings)


def _log_narrative_generation(
    config: NarrativeRuntimeConfig,
    metadata: NarrativeGenerationMetadata,
) -> None:
    mode_requested = config.provider if config.enabled else "disabled"
    log_level = logging.WARNING if metadata.fallback_used else logging.INFO
    logger.log(
        log_level,
        (
            "Narrative generation complete | mode_requested=%s | requested_provider=%s | "
            "actual_provider=%s | generator_name=%s | wall_clock_duration_ms=%s | "
            "fallback_used=%s | fallback_reason=%s"
        ),
        mode_requested,
        metadata.requested_provider,
        metadata.actual_provider,
        metadata.generator_name,
        metadata.wall_clock_duration_ms,
        metadata.fallback_used,
        metadata.fallback_reason or "none",
    )
