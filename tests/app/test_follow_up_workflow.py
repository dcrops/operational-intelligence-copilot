"""AppTests for guided follow-up workflow navigation."""

from __future__ import annotations

import pytest

from tests.app.helpers import (
    assert_findings_reachable,
    assert_no_app_exception,
    assert_question_input,
    ask_question,
    click_follow_up_ask_button,
    load_sample_dataset,
    run_analysis,
)
from tests.app.golden_expectations import get_scenario
from ui.results_headings import TAB_FINDINGS_LABEL, TAB_SUMMARY_LABEL
from ui.state import RESULTS_TABS_SESSION_KEY

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestFollowUpWorkflowNavigation:
    def test_ask_this_scrolls_back_to_question_area(self, app) -> None:
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, "Which production line has the highest defects?")
        run_analysis(app)
        assert_findings_reachable(app)

        click_follow_up_ask_button(app, index=0)

        populated_question = app.text_area(key="question").value
        assert populated_question
        assert "lowest" in populated_question.lower()
        assert app.session_state["scroll_to_question_pending"] is False
        assert_question_input(app, populated_question)

    def test_analysis_resets_results_tab_to_summary(self, app) -> None:
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        app.session_state[RESULTS_TABS_SESSION_KEY] = TAB_FINDINGS_LABEL
        app.run()
        assert app.session_state[RESULTS_TABS_SESSION_KEY] == TAB_FINDINGS_LABEL

        run_analysis(app)

        assert_no_app_exception(app)
        assert app.session_state[RESULTS_TABS_SESSION_KEY] == TAB_SUMMARY_LABEL

    @pytest.mark.parametrize(
        ("dataset_label", "question"),
        [
            ("Manufacturing demo", "Which production line has the highest defects?"),
            ("Education demo", "Which school has the highest behaviour incidents?"),
            ("Workforce demo", "Which department has the highest hours?"),
        ],
    )
    def test_follow_up_then_analyse_returns_to_summary(
        self,
        app,
        dataset_label: str,
        question: str,
    ) -> None:
        load_sample_dataset(app, dataset_label)

        ask_question(app, question)
        run_analysis(app)

        app.session_state[RESULTS_TABS_SESSION_KEY] = TAB_FINDINGS_LABEL
        app.run()

        click_follow_up_ask_button(app, index=0)
        run_analysis(app)

        assert_no_app_exception(app)
        assert app.session_state[RESULTS_TABS_SESSION_KEY] == TAB_SUMMARY_LABEL
