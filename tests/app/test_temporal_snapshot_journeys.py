"""Temporal and snapshot workflow AppTests (Milestone 10f)."""

from __future__ import annotations

import pytest

from tests.app.helpers import assert_journey_outcome, run_golden_scenario

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestTemporalSnapshotJourneys:
    def test_manufacturing_temporal_filter_journey(self, app):
        """
        Manufacturing — Q1 variance question applies a temporal filter, completes
        without clarification, and does not activate snapshot mode.
        """
        run_golden_scenario(app, "manufacturing_temporal_filter_journey")
        assert_journey_outcome(app, "manufacturing_temporal_filter_journey")

    def test_manufacturing_snapshot_analysis_journey(self, app):
        """
        Manufacturing — April snapshot question completes without clarification
        and activates snapshot transparency with executive reasoning.
        """
        run_golden_scenario(app, "manufacturing_snapshot_analysis_journey")
        assert_journey_outcome(app, "manufacturing_snapshot_analysis_journey")

    def test_manufacturing_snapshot_contributors_journey(self, app):
        """
        Manufacturing — April snapshot question with an explicit dimension surfaces
        snapshot contributor transparency.
        """
        run_golden_scenario(app, "manufacturing_snapshot_contributors_journey")
        assert_journey_outcome(app, "manufacturing_snapshot_contributors_journey")
