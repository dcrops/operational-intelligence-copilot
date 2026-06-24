"""Reusable Streamlit AppTest helpers for application journey tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.app.golden_expectations import (
    ExpectedOutcome,
    GoldenQuestion,
    GoldenScenario,
    SECTION_CLARIFICATION,
    SECTION_RESULTS,
    get_scenario,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = PROJECT_ROOT / "app.py"


def require_streamlit_testing() -> None:
    """Skip application tests when Streamlit AppTest is unavailable."""
    pytest.importorskip("streamlit.testing.v1")


def launch_app(*, timeout: int = 90) -> AppTest:
    """Launch the Streamlit application under test."""
    require_streamlit_testing()
    app = AppTest.from_file(str(APP_PATH), default_timeout=timeout)
    app.run()
    assert_no_app_exception(app)
    return app


def assert_no_app_exception(app: AppTest) -> None:
    """Fail when the app script raised during the latest run."""
    assert not app.exception, _format_app_exception(app)


def _format_app_exception(app: AppTest) -> str:
    if not app.exception:
        return ""
    return "; ".join(str(item.value) for item in app.exception)


def user_visible_text(app: AppTest) -> str:
    """Aggregate user-visible markdown and subheader text from the app."""
    parts: list[str] = []
    for element in app.markdown:
        if element.value:
            parts.append(element.value)
    for element in app.subheader:
        if element.value:
            parts.append(element.value)
    return "\n".join(parts)


def assert_section_visible(app: AppTest, section_title: str) -> None:
    """Assert a user-visible report section heading is present."""
    visible = user_visible_text(app)
    assert section_title in visible, (
        f"Expected section {section_title!r} to be visible. "
        f"Visible subheaders: {[s.value for s in app.subheader]}"
    )


def assert_section_hidden(app: AppTest, section_title: str) -> None:
    """Assert a section heading is not currently visible."""
    assert section_title not in user_visible_text(app)


def assert_bootstrap_prompt_visible(app: AppTest) -> None:
    """Assert the app prompts the user to load a dataset."""
    assert any(
        "Upload a CSV in the sidebar or load a sample dataset" in (info.value or "")
        for info in app.info
    )


def assert_dataset_loaded(app: AppTest) -> None:
    """Assert a dataset is present in session state."""
    assert app.session_state["df"] is not None
    assert app.session_state["profile"] is not None


def load_sample_dataset(app: AppTest, sample_label: str) -> AppTest:
    """Load a sidebar sample dataset by its display label."""
    app.sidebar.selectbox(key="sample_dataset_choice").select(sample_label).run()
    _click_sidebar_button(app, "Load selected sample")
    assert_no_app_exception(app)
    assert_dataset_loaded(app)
    return app


def upload_dataset(app: AppTest, csv_path: Path, *, filename: str | None = None) -> AppTest:
    """Upload a CSV through the sidebar file uploader (future upload journeys)."""
    upload_name = filename or csv_path.name
    with csv_path.open("rb") as handle:
        app.sidebar.file_uploader[0].upload({upload_name: handle.read()}).run()
    assert_no_app_exception(app)
    assert_dataset_loaded(app)
    return app


def ask_question(app: AppTest, question: str) -> AppTest:
    """Enter a natural-language question."""
    app.text_area(key="question").input(question).run()
    return app


def run_analysis(app: AppTest) -> AppTest:
    """Submit the current question for analysis."""
    analyze = app.button(key="analyze_question")
    assert not analyze.disabled, "Analyze button is disabled — enter a question first."
    analyze.click().run()
    assert_no_app_exception(app)
    return app


def select_clarification_option(
    app: AppTest,
    option: str,
    *,
    clarification_type: str,
) -> AppTest:
    """Choose a clarification radio option."""
    app.radio(key=f"clarification_{clarification_type}").set_value(option).run()
    return app


def continue_clarification(app: AppTest) -> AppTest:
    """Continue analysis after a clarification selection."""
    app.button(key="continue_clarification").click().run()
    assert_no_app_exception(app)
    return app


def assert_clarification_visible(app: AppTest, *, clarification_type: str | None = None) -> None:
    """Assert the clarification workflow is shown."""
    assert_section_visible(app, SECTION_CLARIFICATION)
    if clarification_type is not None:
        assert app.radio(key=f"clarification_{clarification_type}") is not None


def assert_results_visible(app: AppTest) -> None:
    """Assert the results panel is shown."""
    assert_section_visible(app, SECTION_RESULTS)
    assert not app.error, f"Unexpected app error: {[item.value for item in app.error]}"


def assert_direct_answer(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_DIRECT_ANSWER

    assert_results_visible(app)
    assert_section_visible(app, SECTION_DIRECT_ANSWER)


def assert_operational_assessment(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_OPERATIONAL_ASSESSMENT

    assert_section_visible(app, SECTION_OPERATIONAL_ASSESSMENT)


def assert_executive_reasoning(app: AppTest) -> None:
    from tests.app.golden_expectations import EXECUTIVE_REASONING_HEADING

    assert_section_visible(app, EXECUTIVE_REASONING_HEADING)


def assert_executive_conclusions(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_EXECUTIVE_CONCLUSIONS

    assert_section_visible(app, SECTION_EXECUTIVE_CONCLUSIONS)


def assert_clarification_options_available(app: AppTest, *, clarification_type: str) -> None:
    """Assert the user can choose from multiple clarification options."""
    radio = app.radio(key=f"clarification_{clarification_type}")
    assert radio is not None, f"Expected clarification radio for {clarification_type!r}"
    assert len(radio.options) >= 2, (
        f"Expected multiple clarification options for {clarification_type!r}, "
        f"got {len(radio.options)}"
    )


def assert_clarification_resolved(app: AppTest) -> None:
    """Assert clarification workflow is no longer blocking results."""
    assert_section_hidden(app, SECTION_CLARIFICATION)


def assert_snapshot_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import SNAPSHOT_TRANSPARENCY_MARKER

    assert SNAPSHOT_TRANSPARENCY_MARKER in user_visible_text(app)


def assert_temporal_filter_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import TEMPORAL_FILTER_MARKER

    assert TEMPORAL_FILTER_MARKER in user_visible_text(app)


def assert_snapshot_not_active(app: AppTest) -> None:
    from tests.app.golden_expectations import SNAPSHOT_TRANSPARENCY_MARKER

    assert SNAPSHOT_TRANSPARENCY_MARKER not in user_visible_text(app)


def assert_snapshot_contributors_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import SNAPSHOT_CONTRIBUTORS_MARKER

    visible = user_visible_text(app)
    assert SNAPSHOT_CONTRIBUTORS_MARKER in visible
    assert "Dimension:" in visible
    assert "Highest:" in visible
    assert "Lowest:" in visible


def assert_priority_actions(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_PRIORITY_ACTIONS

    assert_section_visible(app, SECTION_PRIORITY_ACTIONS)


def assert_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_SYSTEM_TRANSPARENCY

    assert_section_visible(app, SECTION_SYSTEM_TRANSPARENCY)


def assert_expected_sections(app: AppTest, sections: tuple[str, ...]) -> None:
    """Assert all expected user-visible sections are present."""
    for section in sections:
        assert_section_visible(app, section)


def _click_sidebar_button(app: AppTest, label: str) -> None:
    button = next(
        (candidate for candidate in app.sidebar.button if candidate.label == label),
        None,
    )
    assert button is not None, f"Sidebar button {label!r} not found."
    button.click().run()


def execute_golden_question(app: AppTest, golden_question: GoldenQuestion) -> AppTest:
    """Ask a golden question and resolve clarification steps when defined."""
    ask_question(app, golden_question.question)
    run_analysis(app)

    if golden_question.clarification_steps:
        for step in golden_question.clarification_steps:
            assert_clarification_visible(app, clarification_type=step.clarification_type)
            assert_clarification_options_available(
                app,
                clarification_type=step.clarification_type,
            )
            if step.option is not None:
                select_clarification_option(
                    app,
                    step.option,
                    clarification_type=step.clarification_type,
                )
            continue_clarification(app)
        assert_clarification_resolved(app)
        assert_results_visible(app)
    elif golden_question.expected_outcome is ExpectedOutcome.CLARIFICATION:
        assert_clarification_visible(app, clarification_type=golden_question.clarification_type)
        assert_clarification_options_available(
            app,
            clarification_type=golden_question.clarification_type,
        )
        return app
    else:
        assert_results_visible(app)
        assert_clarification_resolved(app)

    if golden_question.expects_temporal_filter:
        assert_temporal_filter_transparency(app)

    if golden_question.expects_snapshot:
        assert_snapshot_transparency(app)
    elif golden_question.expects_temporal_filter:
        assert_snapshot_not_active(app)

    if golden_question.expects_snapshot_contributors:
        assert_snapshot_contributors_transparency(app)

    if golden_question.visible_sections:
        assert_expected_sections(app, golden_question.visible_sections)

    return app


def assert_journey_outcome(app: AppTest, scenario_id: str) -> None:
    """Assert the registered behavioural outcome for a golden user journey."""
    scenario = get_scenario(scenario_id)
    question = scenario.question

    assert_no_app_exception(app)

    if question.clarification_steps:
        assert_clarification_resolved(app)
        assert_results_visible(app)
    elif question.expected_outcome is ExpectedOutcome.RESULTS:
        assert_results_visible(app)
        assert_clarification_resolved(app)

    if question.expects_temporal_filter:
        assert_temporal_filter_transparency(app)

    if question.expects_snapshot:
        assert_snapshot_transparency(app)
    elif question.expects_temporal_filter:
        assert_snapshot_not_active(app)

    if question.expects_snapshot_contributors:
        assert_snapshot_contributors_transparency(app)

    if question.visible_sections:
        assert_expected_sections(app, question.visible_sections)


def run_follow_up_question(app: AppTest, golden_question: GoldenQuestion) -> AppTest:
    """Ask a follow-up question and verify analysis completes without clarification."""
    ask_question(app, golden_question.question)
    run_analysis(app)
    assert_clarification_resolved(app)
    assert_results_visible(app)

    if golden_question.visible_sections:
        assert_expected_sections(app, golden_question.visible_sections)

    return app


def assert_clarification_journey_outcome(app: AppTest, scenario_id: str) -> None:
    """Assert clarification resolved and final report behaviour for a journey."""
    scenario = get_scenario(scenario_id)
    final_question = scenario.follow_up_question or scenario.question

    assert_no_app_exception(app)
    assert_clarification_resolved(app)
    assert_results_visible(app)

    if final_question.visible_sections:
        assert_expected_sections(app, final_question.visible_sections)


def run_golden_scenario(app: AppTest, scenario_id: str) -> AppTest:
    """Load a golden dataset and execute its registered question journey."""
    scenario = get_scenario(scenario_id)
    dataset = scenario.dataset

    if dataset.sidebar_label:
        load_sample_dataset(app, dataset.sidebar_label)
    else:
        upload_dataset(app, dataset.csv_path)

    execute_golden_question(app, scenario.question)

    if scenario.follow_up_question is not None:
        run_follow_up_question(app, scenario.follow_up_question)

    return app
