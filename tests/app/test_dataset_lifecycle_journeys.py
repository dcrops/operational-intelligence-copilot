"""Dataset lifecycle AppTests (Milestone 10g).

Dataset reset is not covered because the application does not support clearing
datasets without replacing them.
"""

from __future__ import annotations

import pytest

from tests.app.helpers import assert_journey_outcome, run_golden_scenario

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestDatasetLifecycleJourneys:
    def test_dataset_onboarding_journey(self, app):
        """
        Upload a valid CSV, verify profiling feedback, and complete analysis
        without errors.
        """
        run_golden_scenario(app, "dataset_onboarding_journey")
        assert_journey_outcome(app, "dataset_onboarding_journey")

    def test_dataset_replacement_journey(self, app):
        """
        Analyse one sample dataset, replace it with another, confirm stale
        results are cleared, and complete a new analysis.
        """
        run_golden_scenario(app, "dataset_replacement_journey")
        assert_journey_outcome(app, "dataset_replacement_journey")

    def test_invalid_dataset_recovery_journey(self, app):
        """
        Reject an empty upload while preserving the active dataset and recover
        by re-running analysis.
        """
        run_golden_scenario(app, "dataset_invalid_recovery_journey")
        assert_journey_outcome(app, "dataset_invalid_recovery_journey")
