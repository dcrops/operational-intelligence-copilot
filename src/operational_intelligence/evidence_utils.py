"""Shared helpers for constructing JSON-serializable evidence context."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


def normalize_scalar(value: Any) -> str | int | float | bool | None:
    """Coerce pandas/numpy scalars to native JSON-serializable Python types."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        if isinstance(value, float) and pd.isna(value):
            return None
        return value
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        native = value.item()
        if isinstance(native, bool):
            return native
        if isinstance(native, int):
            return int(native)
        if isinstance(native, float):
            return float(native)
        return native
    if isinstance(value, float):
        return float(value)
    return str(value)


def build_supporting_context(
    base: dict[str, str | int | float | bool | None],
    metric_name: str | None,
    metric_value: float | int | str | None,
) -> dict[str, str | int | float | bool | None]:
    """Return supporting_context with metric value included under metric_name."""
    context = dict(base)
    normalized_metric_value = normalize_scalar(metric_value)
    if metric_name and normalized_metric_value is not None:
        context[metric_name] = normalized_metric_value
    return context


def assert_json_serializable(context: dict[str, str | int | float | bool | None]) -> None:
    """Validate that a supporting_context dict is JSON-serializable."""
    json.dumps(context)
