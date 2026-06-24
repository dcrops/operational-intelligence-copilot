"""Configuration for optional AI narrative generation."""

from __future__ import annotations

import os

_ENV_VAR = "OIC_NARRATIVE_ENABLED"
_ENABLED_VALUES = frozenset({"1", "true", "yes"})


def is_narrative_enabled() -> bool:
    """Return True when optional narrative generation is enabled."""
    return os.environ.get(_ENV_VAR, "").strip().lower() in _ENABLED_VALUES
