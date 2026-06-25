"""Configuration for optional AI narrative generation."""

from __future__ import annotations

import os

from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig

_ENV_ENABLED = "OIC_NARRATIVE_ENABLED"
_ENV_PROVIDER = "OIC_NARRATIVE_PROVIDER"
_ENV_OPENAI_MODEL = "OIC_OPENAI_MODEL"
_ENABLED_VALUES = frozenset({"1", "true", "yes"})

PROVIDER_DETERMINISTIC = "deterministic"
PROVIDER_OPENAI = "openai"
SUPPORTED_PROVIDERS = frozenset({PROVIDER_DETERMINISTIC, PROVIDER_OPENAI})

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def is_narrative_enabled() -> bool:
    """Return True when optional narrative generation is enabled."""
    return os.environ.get(_ENV_ENABLED, "").strip().lower() in _ENABLED_VALUES


def get_narrative_provider() -> str:
    """Return the configured narrative provider, defaulting to deterministic."""
    if not is_narrative_enabled():
        return PROVIDER_DETERMINISTIC

    provider = os.environ.get(_ENV_PROVIDER, "").strip().lower()
    if not provider:
        return PROVIDER_DETERMINISTIC
    if provider in SUPPORTED_PROVIDERS:
        return provider
    return PROVIDER_DETERMINISTIC


def get_openai_provider_config() -> OpenAIProviderConfig:
    """Return OpenAI provider settings from environment."""
    model = os.environ.get(_ENV_OPENAI_MODEL, DEFAULT_OPENAI_MODEL).strip()
    if not model:
        model = DEFAULT_OPENAI_MODEL
    return OpenAIProviderConfig(model=model)
