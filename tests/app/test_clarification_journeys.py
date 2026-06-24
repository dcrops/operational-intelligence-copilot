"""Clarification workflow AppTests (Milestone 10e)."""

from __future__ import annotations

import pytest

from tests.app.helpers import (
    assert_clarification_journey_outcome,
    run_golden_scenario,
)

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestClarificationWorkflowJourneys:
    def test_education_metric_clarification_journey(self, app):
        """
        Education — ambiguous performance question requests metric clarification,
        user selects a metric, and the report renders without stale clarification UI.
        """
        run_golden_scenario(app, "education_metric_clarification_journey")
        assert_clarification_journey_outcome(app, "education_metric_clarification_journey")

    def test_education_dimension_clarification_journey(self, app):
        """
        Education — causal question requests dimension clarification first,
        user selects a grouping field, and analysis completes successfully.
        """
        run_golden_scenario(app, "education_dimension_clarification_journey")
        assert_clarification_journey_outcome(app, "education_dimension_clarification_journey")

    def test_workforce_clarification_recovery_journey(self, app):
        """
        Workforce — resolve metric clarification, then ask a second resolved question
        without clarification UI or application errors.
        """
        run_golden_scenario(app, "workforce_clarification_recovery_journey")
        assert_clarification_journey_outcome(app, "workforce_clarification_recovery_journey")
