import pytest

from src.operational_intelligence.models import EvidenceItem, Finding
from ui.anomaly_presentation import anomaly_business_description, anomaly_direction_label

pytestmark = pytest.mark.unit


def _anomaly_finding(items: list[EvidenceItem]) -> Finding:
    return Finding(
        title="Anomalies Detected by Anomaly Detection Tool",
        description="Anomalies were detected.",
        severity="HIGH",
        confidence="HIGH",
        evidence=items,
    )


def _anomaly_item(direction: str, value: float, row_index: int = 0) -> EvidenceItem:
    return EvidenceItem(
        description=f"Anomalous value in row {row_index}",
        metric_name="units_produced",
        metric_value=value,
        supporting_context={
            "row_index": row_index,
            "mean": 500.0,
            "standard_deviation": 100.0,
            "z_score": 2.5 if direction == "HIGH" else -2.5,
            "anomaly_direction": direction,
        },
    )


def test_all_high_anomalies_use_high_direction():
    finding = _anomaly_finding(
        [_anomaly_item("HIGH", 900 + index, index) for index in range(38)]
    )

    assert anomaly_direction_label(finding) == "high"
    assert "38 unusually high values" in anomaly_business_description(
        finding,
        "units produced",
    )


def test_all_low_anomalies_use_low_direction():
    finding = _anomaly_finding(
        [_anomaly_item("LOW", 100 + index, index) for index in range(38)]
    )

    assert anomaly_direction_label(finding) == "low"
    assert "38 unusually low values" in anomaly_business_description(
        finding,
        "units produced",
    )


def test_mixed_anomalies_align_with_extreme_item_direction():
    finding = _anomaly_finding(
        [_anomaly_item("LOW", 100 + index, index) for index in range(30)]
        + [_anomaly_item("HIGH", 900 + index, 30 + index) for index in range(8)]
    )

    assert anomaly_direction_label(finding) == "high"
    assert "38 unusually high values" in anomaly_business_description(
        finding,
        "units produced",
    )
