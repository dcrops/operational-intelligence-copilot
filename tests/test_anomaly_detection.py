import pandas as pd
import pytest

from src.operational_intelligence.anomaly_detection import AnomalyDetectionTool
from tests.support.factories import make_workforce_df

pytestmark = pytest.mark.unit


def test_anomaly_evidence_includes_observed_metric_value_and_stats():
    df = make_workforce_df()
    result = AnomalyDetectionTool().analyze(df, "overtime_hours", threshold=1.5)

    assert result.success is True
    assert result.evidence_items

    item = result.evidence_items[0]
    assert item.metric_name == "overtime_hours"
    assert item.supporting_context["overtime_hours"] == item.metric_value
    assert isinstance(item.supporting_context["row_index"], int)
    assert "mean" in item.supporting_context
    assert "standard_deviation" in item.supporting_context
    assert "z_score" in item.supporting_context
    assert item.supporting_context["anomaly_direction"] in {"HIGH", "LOW"}


def test_anomaly_evidence_row_index_is_native_int():
    df = pd.DataFrame({"hours": [10.0, 10.0, 10.0, 100.0]})
    result = AnomalyDetectionTool().analyze(df, "hours", threshold=1.0)

    assert result.evidence_items
    row_index = result.evidence_items[0].supporting_context["row_index"]
    assert isinstance(row_index, int)
