"""Shared helpers for presenting internal metric identifiers in the UI."""

from __future__ import annotations

import re

_SNAKE_CASE_PATTERN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")


def humanise_metric_name(identifier: str) -> str:
    """Convert an internal metric identifier into a presentation label."""
    cleaned = identifier.strip().replace("_", " ")
    return " ".join(word.capitalize() for word in cleaned.split())


def humanise_user_facing_text(text: str) -> str:
    """Replace snake_case metric identifiers embedded in user-facing text."""

    def replacer(match: re.Match[str]) -> str:
        return humanise_metric_name(match.group(0))

    return _SNAKE_CASE_PATTERN.sub(replacer, text)


def humanise_metric_references_in_text(
    text: str,
    metric_names: list[str],
) -> str:
    """Replace known metric identifiers and snake_case tokens with presentation labels."""
    result = text
    for name in sorted({name.strip() for name in metric_names if name.strip()}, key=len, reverse=True):
        label = humanise_metric_name(name)
        variants = {name, name.replace("_", " "), label.lower()}
        for variant in variants:
            if not variant or variant == label:
                continue
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            result = pattern.sub(label, result)
    return humanise_user_facing_text(result)
