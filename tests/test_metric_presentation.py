"""Tests for shared metric presentation helpers."""

from __future__ import annotations

import pytest

from ui.metric_presentation import (
    humanise_metric_name,
    humanise_metric_references_in_text,
    humanise_user_facing_text,
)

pytestmark = pytest.mark.unit


class TestMetricPresentation:
    def test_humanise_metric_name_converts_snake_case(self):
        assert humanise_metric_name("attendance_rate") == "Attendance Rate"
        assert humanise_metric_name("units_produced") == "Units Produced"
        assert humanise_metric_name("overtime_hours") == "Overtime Hours"
        assert humanise_metric_name("employee_count") == "Employee Count"

    def test_humanise_user_facing_text_replaces_embedded_snake_case(self):
        text = "Review snapshot performance for attendance_rate against baseline."

        assert humanise_user_facing_text(text) == (
            "Review snapshot performance for Attendance Rate against baseline."
        )

    def test_humanise_metric_references_in_text_replaces_known_metrics(self):
        text = "Investigate whether attendance rate changes are concentrated in specific periods."

        result = humanise_metric_references_in_text(
            text,
            ["attendance_rate"],
        )

        assert result == (
            "Investigate whether Attendance Rate changes are concentrated in specific periods."
        )

    def test_humanise_metric_references_in_text_handles_snake_case_and_spaced_variants(self):
        text = "Monitor trend movement linked to overtime_hours."

        result = humanise_metric_references_in_text(
            text,
            ["overtime_hours"],
        )

        assert result == "Monitor trend movement linked to Overtime Hours."
