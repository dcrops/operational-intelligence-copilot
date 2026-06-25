"""Domain-agnostic translation from analytical telemetry to executive language."""

from __future__ import annotations

import re

_SNAKE_CASE_PATTERN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
_ANALYZED_COLUMN_PATTERN = re.compile(
    r"Analyzed column '([^']+)' for anomalies using z-score threshold [^.\n]+\.\s*",
    re.IGNORECASE,
)
_Z_SCORE_PAREN_PATTERN = re.compile(
    r"\(\s*z-score\s+[-+]?\d+(?:\.\d+)?\s*\)",
    re.IGNORECASE,
)
_Z_SCORE_INLINE_PATTERN = re.compile(
    r"\bz-score\s+[-+]?\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
_Z_SCORE_THRESHOLD_PATTERN = re.compile(
    r"z-score threshold\s+[-+]?\d+(?:\.\d+)?",
    re.IGNORECASE,
)
_QUOTED_IDENTIFIER_PATTERN = re.compile(r"'([^']+)'")
_IMPLEMENTATION_TOOL_PATTERN = re.compile(r"\s+tool\b", re.IGNORECASE)
_FINDING_TITLE_TOOL_PATTERNS = (
    re.compile(r"^Anomalies Detected by .+$", re.IGNORECASE),
    re.compile(r"^Significant Variance Identified by .+$", re.IGNORECASE),
    re.compile(r"^Trend Identified by .+$", re.IGNORECASE),
    re.compile(r"^Snapshot Summary from .+$", re.IGNORECASE),
    re.compile(r"^Analysis Failure(?: Linked)?(?: to .+)?$", re.IGNORECASE),
)
_ANALYTICAL_TELEMETRY_PATTERNS = (
    re.compile(r"Operational analysis identified[^.]*\.\s*", re.IGNORECASE),
    re.compile(
        r"\d+\s+unusual\s+(?:high|low\s+)?values?\s+were\s+detected[^.]*\.\s*",
        re.IGNORECASE,
    ),
    re.compile(r"Unusual values were identified for[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Examples include:\s*", re.IGNORECASE),
    re.compile(r"Affected records:\s*", re.IGNORECASE),
    re.compile(r"See supporting evidence for[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"\bfinding\(s\)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+additional\s+unusual\s+records?\s+were\s+also\s+identified\.?\s*", re.IGNORECASE),
)
_ORPHAN_NUMBER_FRAGMENT = re.compile(r"\.\s+\d+\.(?:\s|$)")
_BULLET_PREFIX = re.compile(r"^\s*-\s*", re.MULTILINE)


def humanize_identifier(identifier: str) -> str:
    """Convert an internal identifier into presentation text."""
    cleaned = identifier.strip().replace("_", " ")
    return " ".join(word.capitalize() for word in cleaned.split())


def translate_technical_language(text: str) -> str:
    """Replace analytical implementation wording with executive phrasing."""
    if not text.strip():
        return text

    translated = text
    translated = _ANALYZED_COLUMN_PATTERN.sub(
        lambda match: (
            f"Performance for {humanize_identifier(match.group(1))} appears outside normal expectations. "
        ),
        translated,
    )
    translated = _Z_SCORE_PAREN_PATTERN.sub(
        "(far outside the normal operating range)",
        translated,
    )
    translated = _Z_SCORE_INLINE_PATTERN.sub(
        "result far outside the normal operating range",
        translated,
    )
    translated = _Z_SCORE_THRESHOLD_PATTERN.sub(
        "expected operating range",
        translated,
    )
    translated = re.sub(
        r"\bstandard deviation\b",
        "expected variation",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\banomaly threshold\b",
        "expected operating range",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\busing z-score method\b",
        "",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\bdetected using z-score\b",
        "identified as unusual compared with normal patterns",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\banomaly detection\b",
        "unusual performance pattern",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\banomalous records?\b",
        "unusual records",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\bunusual value identification\b",
        "unusual performance pattern",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(r"\s{2,}", " ", translated)
    translated = re.sub(r" \.", ".", translated)
    return humanize_embedded_identifiers(translated.strip())


def is_implementation_title(text: str) -> bool:
    """Return True when text is an internal analytical tool title."""
    cleaned = text.strip()
    if not cleaned:
        return False
    if _IMPLEMENTATION_TOOL_PATTERN.search(cleaned):
        return True
    return any(pattern.match(cleaned) for pattern in _FINDING_TITLE_TOOL_PATTERNS)


def strip_implementation_wording(text: str) -> str:
    """Remove internal tool names and implementation labels from executive prose."""
    if not text.strip():
        return text

    cleaned = _IMPLEMENTATION_TOOL_PATTERN.sub("", text)
    cleaned = re.sub(
        r"Anomalies Detected by .+",
        "Significant performance anomalies",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"Significant Variance Identified by .+",
        "Significant performance differences",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"Trend Identified by .+",
        "Significant performance trends",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"Snapshot Summary from .+",
        "Snapshot performance summary",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def strip_analytical_telemetry(text: str) -> str:
    """Remove analytical count and process wording from executive prose."""
    cleaned = text
    for pattern in _ANALYTICAL_TELEMETRY_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(
        r"\b\d+\s+unusual\s+(?:high|low\s+)?values?\s+were\s+detected\b",
        "Performance appears outside normal expectations",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\boperational analysis identified\b",
        "The analysis indicates",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def sanitize_executive_prose(text: str) -> str:
    """Normalize spacing and remove common executive formatting artefacts."""
    if not text.strip():
        return text

    cleaned = _BULLET_PREFIX.sub("", text)
    cleaned = _ORPHAN_NUMBER_FRAGMENT.sub(". ", cleaned)
    cleaned = re.sub(r"([A-Za-z])\.\s+(\d+)\.$", r"\1.", cleaned)
    cleaned = re.sub(r"\s+\.", ".", cleaned)
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+,", ",", cleaned)
    return cleaned.strip()


def humanize_embedded_identifiers(text: str) -> str:
    """Humanize snake_case identifiers embedded in translated text."""

    def replacer(match: re.Match[str]) -> str:
        return humanize_identifier(match.group(0))

    return _SNAKE_CASE_PATTERN.sub(replacer, text)


def collapse_multiline_text(text: str) -> str:
    """Collapse structured direct answers into executive prose."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    return " ".join(lines)


def split_sentences(text: str) -> list[str]:
    """Split prose into sentence-like fragments."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def is_analytical_telemetry(text: str) -> bool:
    """Return True when text is primarily analytical process wording."""
    lower = text.lower().strip()
    if not lower:
        return True
    telemetry_markers = (
        "operational analysis identified",
        "finding(s)",
        "examples include",
        "affected records",
        "unusual values were identified for",
        "were detected for",
        "high priority",
        "medium priority",
        "low priority",
    )
    return any(marker in lower for marker in telemetry_markers)


def extract_quoted_identifiers(text: str) -> tuple[str, ...]:
    """Return unique quoted identifiers found in analytical text."""
    seen: set[str] = set()
    identifiers: list[str] = []
    for match in _QUOTED_IDENTIFIER_PATTERN.finditer(text):
        identifier = match.group(1).strip()
        if not identifier:
            continue
        key = identifier.lower()
        if key in seen:
            continue
        seen.add(key)
        identifiers.append(identifier)
    return tuple(identifiers)


def extract_snake_case_identifiers(text: str) -> tuple[str, ...]:
    """Return unique snake_case identifiers found in analytical text."""
    seen: set[str] = set()
    identifiers: list[str] = []
    for match in _SNAKE_CASE_PATTERN.finditer(text):
        identifier = match.group(0)
        key = identifier.lower()
        if key in seen:
            continue
        seen.add(key)
        identifiers.append(identifier)
    return tuple(identifiers)
