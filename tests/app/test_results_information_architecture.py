"""AppTests for Milestone 13b executive results information architecture."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import (
    SECTION_AUDIT,
    SECTION_INVESTIGATION,
    SECTION_OVERVIEW,
    get_scenario,
)
from tests.app.helpers import (
    assert_analysis_header_visible,
    assert_direct_answer,
    assert_executive_reasoning,
    assert_generation_method_visible,
    assert_narrative_content_visible,
    assert_results_information_architecture,
    assert_section_visible,
    assert_transparency,
    ask_question,
    load_sample_dataset,
    run_analysis,
    select_narrative_mode,
    user_visible_text,
)
from ui.narrative_presentation import GENERATED_BY_HEADING, GOVERNANCE_CAPTION, TECHNICAL_DETAILS_HEADING
from ui.narrative_runtime import NARRATIVE_MODE_DETERMINISTIC

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestResultsInformationArchitecture:
    def test_analysis_header_and_section_order(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_analysis_header_visible(app)
        assert_results_information_architecture(app)
        assert_direct_answer(app)
        assert_section_visible(app, SECTION_OVERVIEW)
        assert_section_visible(app, SECTION_INVESTIGATION)
        assert_section_visible(app, SECTION_AUDIT)

    def test_executive_content_precedes_investigation(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        visible = user_visible_text(app)
        navigation_index = visible.index("Results Navigation")
        assert visible.index("Executive Summary") < visible.index("Investigation", navigation_index)

    def test_audit_contains_verification_and_transparency(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        visible = user_visible_text(app)
        audit_index = visible.index(SECTION_AUDIT, visible.index("Results Navigation"))
        assert visible.index("System Transparency") > audit_index
        assert visible.index("Verification") > audit_index
        assert GENERATED_BY_HEADING in visible
        assert GOVERNANCE_CAPTION in visible
        assert any(
            item.label == TECHNICAL_DETAILS_HEADING for item in app.expander
        )

    def test_analytical_capabilities_preserved(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_executive_reasoning(app)
        assert_transparency(app)
        assert_narrative_content_visible(app)
        assert_generation_method_visible(app, "Deterministic Engine")
