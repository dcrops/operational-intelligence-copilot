"""AppTests for guided follow-up question buttons in the Findings tab."""

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

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestFollowUpQuestionButtons:
    def test_ask_this_populates_question_without_auto_run(self, app) -> None:
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        original_question = "Which production line has the highest defects?"
        ask_question(app, original_question)
        run_analysis(app)
        assert_findings_reachable(app)

        click_follow_up_ask_button(app, index=0)

        populated_question = app.text_area(key="question").value
        assert populated_question
        assert populated_question != original_question
        assert "lowest" in populated_question.lower()
        assert_question_input(app, populated_question)
        assert app.session_state["question"] == populated_question

    def test_ask_this_follow_up_runs_successfully_after_analyse(self, app) -> None:
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, "Which production line has the highest defects?")
        run_analysis(app)

        click_follow_up_ask_button(app, index=0)
        run_analysis(app)

        assert_no_app_exception(app)
        assert app.session_state.last_result is not None
        assert app.session_state.last_result.clarification is None
