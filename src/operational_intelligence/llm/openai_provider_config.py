"""Immutable configuration for OpenAI narrative generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIProviderConfig:
    """Small OpenAI provider settings injected into the narrative adapter."""

    model: str
    temperature: float = 0.0
    timeout_seconds: int = 30
