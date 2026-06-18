"""Golden user journey tests (Milestone 10d — Phase 1)."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import get_scenario
from tests.app.helpers import (
    assert_journey_outcome,
    execute_golden_question,
    load_sample_dataset,
    run_golden_scenario,
)

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestGoldenUserJourneys:
    def test_manufacturing_analysis_journey(self, app):
        """
        Manufacturing — load sample, ask for broad analysis, resolve metric and
        dimension clarification, and verify the full executive report.
        """
        run_golden_scenario(app, "manufacturing_analysis_journey")
        assert_journey_outcome(app, "manufacturing_analysis_journey")

    def test_education_snapshot_journey(self, app):
        """
        Education — ask an April snapshot question with no clarification and
        verify direct answer, executive reasoning, and snapshot transparency.
        """
        run_golden_scenario(app, "education_snapshot_journey")
        assert_journey_outcome(app, "education_snapshot_journey")

    def test_workforce_clarification_journey(self, app):
        """
        Workforce — ask an ambiguous performance question, select a metric during
        clarification, and verify executive reasoning is rendered.
        """
        scenario = get_scenario("workforce_clarification_journey")
        load_sample_dataset(app, scenario.dataset.sidebar_label)
        execute_golden_question(app, scenario.question)
        assert_journey_outcome(app, "workforce_clarification_journey")
