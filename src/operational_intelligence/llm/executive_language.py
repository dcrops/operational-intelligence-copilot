"""Domain-agnostic translation from analytical telemetry to executive language."""

from __future__ import annotations

from src.operational_intelligence.llm.business_narrative_translation import (
    BusinessNarrativeTranslator,
    collapse_multiline_text,
    extract_quoted_identifiers,
    extract_snake_case_identifiers,
    is_analytical_telemetry,
    is_implementation_title,
    sanitize_executive_prose,
    split_sentences,
)

_DEFAULT_TRANSLATOR = BusinessNarrativeTranslator()


def humanize_identifier(identifier: str) -> str:
    """Convert an internal identifier into presentation text."""
    return _DEFAULT_TRANSLATOR.translate_identifier(identifier)


def translate_technical_language(text: str) -> str:
    """Replace analytical implementation wording with executive phrasing."""
    return _DEFAULT_TRANSLATOR.translate_prose(text)


def strip_implementation_wording(text: str) -> str:
    """Remove internal tool names and implementation labels from executive prose."""
    if not text.strip():
        return text
    return _DEFAULT_TRANSLATOR.translate_prose(text)


def strip_analytical_telemetry(text: str) -> str:
    """Remove analytical count and process wording from executive prose."""
    if not text.strip():
        return text
    cleaned = text
    for pattern in _DEFAULT_TRANSLATOR.registry.prose_remove_patterns:
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip()


def humanize_embedded_identifiers(text: str) -> str:
    """Humanize snake_case identifiers embedded in translated text."""
    return _DEFAULT_TRANSLATOR._translate_embedded_identifiers(text)
