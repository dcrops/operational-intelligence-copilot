"""AppTests for Milestone 13c progressive disclosure (superseded by 13d tabs)."""

from __future__ import annotations

import pytest

from tests.app.test_results_tabs import TestResultsTabs

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestProgressiveDisclosure(TestResultsTabs):
    """Backward-compatible alias while tests migrate to tab terminology."""

    pass
