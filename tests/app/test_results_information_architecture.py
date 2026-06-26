"""AppTests for Milestone 13b executive results information architecture."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import get_scenario
from tests.app.helpers import (
    assert_analysis_header_visible,
    assert_audit_reachable,
    assert_direct_answer,
    assert_executive_surface_visible,
    assert_generation_method_visible,
    assert_investigation_collapsed_by_default,
    assert_investigation_reachable,
    assert_narrative_content_reachable,
    assert_results_information_architecture,
    ask_question,
    load_sample_dataset,
    run_analysis,
    select_narrative_mode,
)
from ui.narrative_runtime import NARRATIVE_MODE_DETERMINISTIC

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestResultsInformationArchitecture:
    def test_analysis_header_and_reachable_hierarchy(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_analysis_header_visible(app)
        assert_executive_surface_visible(app)
        assert_investigation_collapsed_by_default(app)
        assert_results_information_architecture(app)
        assert_direct_answer(app)
        assert_investigation_reachable(app)
        assert_audit_reachable(app)

    def test_executive_surface_precedes_disclosure_groups(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_executive_surface_visible(app)
        assert_investigation_collapsed_by_default(app)

    def test_analytical_capabilities_preserved(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_investigation_reachable(app)
        assert_audit_reachable(app)
        assert_narrative_content_reachable(app)
        assert_generation_method_visible(app, "Deterministic Engine")
