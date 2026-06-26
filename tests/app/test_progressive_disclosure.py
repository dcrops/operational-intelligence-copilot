"""AppTests for Milestone 13c progressive disclosure."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import (
    ANALYTICAL_FINDINGS_HEADING,
    SECTION_DATASET_PREVIEW,
    SECTION_SYSTEM_TRANSPARENCY,
    get_scenario,
)
from tests.app.helpers import (
    assert_audit_collapsed_by_default,
    assert_audit_reachable,
    assert_executive_surface_visible,
    assert_expander_present,
    assert_investigation_collapsed_by_default,
    assert_investigation_reachable,
    assert_section_hidden,
    assert_section_visible,
    ask_question,
    expand_disclosure,
    find_expander,
    load_sample_dataset,
    run_analysis,
    select_narrative_mode,
    user_visible_text,
)
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_WHY_THIS_MATTERS,
)
from ui.narrative_presentation import GENERATED_BY_HEADING, LIMITATIONS_HEADING
from ui.narrative_runtime import NARRATIVE_MODE_DETERMINISTIC, NARRATIVE_MODE_OPENAI
from ui.results_headings import DISCLOSURE_AUDIT_LABEL, DISCLOSURE_INVESTIGATION_LABEL

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestProgressiveDisclosure:
    def test_executive_surface_visible_by_default(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_executive_surface_visible(app)
        assert_investigation_collapsed_by_default(app)
        assert_audit_collapsed_by_default(app)
        assert ADVISOR_SECTION_WHY_THIS_MATTERS not in user_visible_text(app)
        assert LIMITATIONS_HEADING not in user_visible_text(app)

    def test_investigation_and_audit_reachable(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_investigation_reachable(app)
        assert_audit_reachable(app)
        assert GENERATED_BY_HEADING in user_visible_text(app)

    def test_dataset_preview_collapses_after_analysis(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        assert_section_visible(app, SECTION_DATASET_PREVIEW)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_expander_present(app, "Dataset Preview", expanded=False)
        expand_disclosure(app, "Dataset Preview")
        assert app.dataframe, "Expected dataset preview dataframe after expanding preview."

    def test_fallback_warning_visible_without_opening_audit(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_OPENAI)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert any(
            "OpenAI mode selected but no API key was found" in (warning.value or "")
            for warning in app.warning
        )
        assert find_expander(app, DISCLOSURE_AUDIT_LABEL) is not None
        assert find_expander(app, DISCLOSURE_INVESTIGATION_LABEL) is not None
