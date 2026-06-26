"""AppTests for Milestone 13d results tabs."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import (
    ANALYTICAL_FINDINGS_HEADING,
    SECTION_DATASET_PREVIEW,
    SECTION_DIRECT_ANSWER,
    SECTION_EXECUTIVE_SUMMARY,
    SECTION_SYSTEM_TRANSPARENCY,
    get_scenario,
)
from tests.app.helpers import (
    assert_audit_reachable,
    assert_audit_tab_not_on_summary,
    assert_expander_present,
    assert_findings_reachable,
    assert_findings_tab_not_on_summary,
    assert_results_tabs_present,
    assert_section_visible,
    assert_summary_tab_visible,
    ask_question,
    expand_disclosure,
    find_results_tab,
    load_sample_dataset,
    run_analysis,
    select_narrative_mode,
    tab_user_visible_text,
)
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_WHY_THIS_MATTERS,
)
from ui.narrative_presentation import GENERATED_BY_HEADING, LIMITATIONS_HEADING
from ui.narrative_runtime import NARRATIVE_MODE_DETERMINISTIC, NARRATIVE_MODE_OPENAI
from ui.results_headings import TAB_AUDIT_LABEL, TAB_FINDINGS_LABEL, TAB_SUMMARY_LABEL

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestResultsTabs:
    def test_results_tabs_present_after_analysis(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_results_tabs_present(app)

    def test_summary_tab_default_content(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_summary_tab_visible(app)
        summary_tab = find_results_tab(app, TAB_SUMMARY_LABEL)
        assert summary_tab is not None
        summary_text = tab_user_visible_text(summary_tab)
        assert ADVISOR_SECTION_WHY_THIS_MATTERS not in summary_text
        assert LIMITATIONS_HEADING not in summary_text

    def test_findings_and_audit_scoped_to_tabs(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_DETERMINISTIC)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_findings_tab_not_on_summary(app)
        assert_audit_tab_not_on_summary(app)
        assert_findings_reachable(app)
        assert_audit_reachable(app)

        summary_tab = find_results_tab(app, TAB_SUMMARY_LABEL)
        findings_tab = find_results_tab(app, TAB_FINDINGS_LABEL)
        audit_tab = find_results_tab(app, TAB_AUDIT_LABEL)
        assert summary_tab is not None and findings_tab is not None and audit_tab is not None
        assert SECTION_DIRECT_ANSWER in tab_user_visible_text(summary_tab)
        assert SECTION_EXECUTIVE_SUMMARY in tab_user_visible_text(summary_tab)
        assert ANALYTICAL_FINDINGS_HEADING in tab_user_visible_text(findings_tab)
        assert SECTION_SYSTEM_TRANSPARENCY in tab_user_visible_text(audit_tab)
        assert GENERATED_BY_HEADING in tab_user_visible_text(audit_tab)

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

    def test_fallback_warning_visible_on_summary_without_audit_tab(self, app) -> None:
        select_narrative_mode(app, NARRATIVE_MODE_OPENAI)
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert any(
            "OpenAI mode selected but no API key was found" in (warning.value or "")
            for warning in app.warning
        )
        assert_results_tabs_present(app)
        summary_tab = find_results_tab(app, TAB_SUMMARY_LABEL)
        assert summary_tab is not None
        assert GENERATED_BY_HEADING not in tab_user_visible_text(summary_tab)
