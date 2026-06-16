import pandas as pd
import pytest

from src.operational_intelligence.trend_analysis import (
    TrendAnalysisTool,
    _classify_trend,
)

pytestmark = pytest.mark.unit


def _analyze_series(values: list[float]) -> tuple[str, str]:
    dates = pd.date_range("2026-01-01", periods=len(values), freq="MS")
    df = pd.DataFrame({"month": dates, "hours": values})
    result = TrendAnalysisTool().analyze(df, "month", "hours")
    assert result.success is True
    classification = result.evidence_items[-1].supporting_context
    return classification["trend_label"], result.summary


def test_classify_increasing_monotonic():
    label, _ = _analyze_series([100, 130, 160, 190, 220])
    assert label == "increasing"


def test_classify_increasing_noisy_upward():
    label, summary = _analyze_series([100, 115, 108, 125, 118, 140])
    assert label == "increasing"
    assert "increased" in summary


def test_classify_decreasing():
    label, summary = _analyze_series([220, 190, 160, 130, 100])
    assert label == "decreasing"
    assert "decreased" in summary


def test_classify_stable():
    label, summary = _analyze_series([150, 152, 149, 151, 150])
    assert label == "stable"
    assert "remained stable" in summary


def test_classify_volatile_alternating_flat_net():
    label, summary = _analyze_series([100, 500, 100, 500, 100])
    assert label == "volatile"
    assert "volatile" in summary


def test_classify_volatile_alternating_large_range():
    label, summary = _analyze_series([100, 500, 100, 500, 100, 500])
    assert label == "volatile"
    assert "volatile" in summary


def test_classify_high_range_monotonic_increasing():
    label, _ = _analyze_series([1000, 1500, 2000, 2500, 3000])
    assert label == "increasing"


def test_short_series_adds_warning():
    dates = pd.date_range("2026-01-01", periods=2, freq="MS")
    df = pd.DataFrame({"month": dates, "hours": [100, 120]})
    result = TrendAnalysisTool().analyze(df, "month", "hours")

    assert result.success is True
    assert any("Fewer than 3 periods" in warning for warning in result.warnings)


def test_aggregate_classification_evidence_included():
    dates = pd.date_range("2026-01-01", periods=4, freq="MS")
    df = pd.DataFrame({"month": dates, "hours": [100, 130, 160, 190]})
    result = TrendAnalysisTool().analyze(df, "month", "hours")

    assert len(result.evidence_items) == 5
    aggregate = result.evidence_items[-1]
    assert aggregate.description.startswith("Trend classification summary")
    assert aggregate.supporting_context["trend_label"] == "increasing"
    assert aggregate.supporting_context["reversals"] == 0


def test_classify_trend_unit_cases():
    assert _classify_trend([100, 130, 160, 190]).trend_label == "increasing"
    assert _classify_trend([100, 500, 100, 500, 100]).trend_label == "volatile"
    assert _classify_trend([100, 115, 108, 125, 118, 140]).trend_label == "increasing"
