import json

import numpy as np
import pandas as pd
import pytest

from src.operational_intelligence.evidence_utils import (
    assert_json_serializable,
    build_supporting_context,
    normalize_scalar,
)

pytestmark = pytest.mark.unit


def test_build_supporting_context_adds_metric_key():
    context = build_supporting_context(
        {"month": "2026-01-01", "aggregation": "mean"},
        "attendance_rate",
        89.82,
    )

    assert context["month"] == "2026-01-01"
    assert context["aggregation"] == "mean"
    assert context["attendance_rate"] == 89.82
    assert_json_serializable(context)


def test_build_supporting_context_skips_none_metric_value():
    context = build_supporting_context(
        {"school": "School E"},
        "attendance_rate",
        None,
    )

    assert "attendance_rate" not in context
    assert context["school"] == "School E"


def test_build_supporting_context_coerces_pandas_and_numpy_scalars():
    context = build_supporting_context(
        {"aggregation": "sum"},
        "hours",
        pd.Series([600.0]).iloc[0],
    )

    assert context["hours"] == 600.0
    assert isinstance(context["hours"], float)
    assert_json_serializable(context)

    numpy_context = build_supporting_context(
        {"aggregation": "mean"},
        "attendance_rate",
        np.float64(83.66),
    )
    assert numpy_context["attendance_rate"] == 83.66
    assert isinstance(numpy_context["attendance_rate"], float)


def test_normalize_scalar_returns_native_int_for_row_index():
    assert normalize_scalar(np.int64(6)) == 6
    assert isinstance(normalize_scalar(np.int64(6)), int)


def test_json_serializable_output_round_trips():
    context = build_supporting_context(
        {
            "row_index": 6,
            "aggregation": "mean",
            "is_comparison_target": True,
        },
        "attendance_rate",
        51.0,
    )
    serialized = json.dumps(context)
    restored = json.loads(serialized)
    assert restored["attendance_rate"] == 51.0
    assert restored["is_comparison_target"] is True
