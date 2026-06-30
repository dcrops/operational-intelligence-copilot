"""Reusable Streamlit AppTest helpers for application journey tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.app.golden_expectations import (
    APP_SHELL_BADGE_FRAGMENT,
    APP_SHELL_BRAND,
    APP_SHELL_SIDEBAR_PLATFORM,
    APP_SHELL_SUBTITLE_FRAGMENT,
    APP_SHELL_TITLE,
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
    for element in app.caption:
        if element.value:
            parts.append(element.value)
    for element in app.success:
        if element.value:
            parts.append(element.value)
    for element in app.warning:
        if element.value:
            parts.append(element.value)
    return "\n".join(parts)


def tab_user_visible_text(tab) -> str:
    """Aggregate user-visible text from a single results tab block."""
    parts: list[str] = []
    for element in tab.markdown:
        if element.value:
            parts.append(element.value)
    for element in tab.subheader:
        if element.value:
            parts.append(element.value)
    for element in tab.caption:
        if element.value:
            parts.append(element.value)
    for element in tab.success:
        if element.value:
            parts.append(element.value)
    for element in tab.warning:
        if element.value:
            parts.append(element.value)
    return "\n".join(parts)


def results_tabs_visible_text(app: AppTest) -> str:
    """Aggregate user-visible text across all results tabs."""
    if not app.tabs:
        return user_visible_text(app)
    return "\n".join(tab_user_visible_text(tab) for tab in app.tabs)


def sidebar_visible_text(app: AppTest) -> str:
    """Aggregate user-visible sidebar text for lifecycle assertions."""
    parts: list[str] = []
    sidebar = app.sidebar
    for element in sidebar.markdown:
        if element.value:
            parts.append(element.value)
    for element in sidebar.subheader:
        if element.value:
            parts.append(element.value)
    for element in sidebar.caption:
        if element.value:
            parts.append(element.value)
    for element in sidebar.error:
        if element.value:
            parts.append(element.value)
    for element in sidebar.success:
        if element.value:
            parts.append(element.value)
    for element in sidebar.warning:
        if element.value:
            parts.append(element.value)
    for element in sidebar.metric:
        if element.label:
            parts.append(element.label)
        if element.value is not None:
            parts.append(str(element.value))
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
    visible = user_visible_text(app)
    assert "Upload a CSV in the sidebar or load a sample dataset" in visible


def assert_bootstrap_prompt_hidden(app: AppTest) -> None:
    """Assert the bootstrap dataset prompt is not shown."""
    visible = user_visible_text(app)
    assert "Upload a CSV in the sidebar or load a sample dataset" not in visible


def assert_app_shell_visible(app: AppTest) -> None:
    """Assert branded application shell content is visible."""
    visible = user_visible_text(app)
    assert APP_SHELL_TITLE in visible, f"Expected app title {APP_SHELL_TITLE!r} in hero."
    assert APP_SHELL_BRAND in visible, f"Expected brand label {APP_SHELL_BRAND!r} in hero."
    assert APP_SHELL_SUBTITLE_FRAGMENT in visible, (
        "Expected hero subtitle fragment in visible text."
    )
    assert APP_SHELL_BADGE_FRAGMENT in visible, (
        "Expected at least one capability badge in visible text."
    )

    sidebar = sidebar_visible_text(app)
    assert APP_SHELL_BRAND in sidebar, f"Expected brand label {APP_SHELL_BRAND!r} in sidebar."
    assert APP_SHELL_SIDEBAR_PLATFORM in sidebar, (
        f"Expected sidebar platform label {APP_SHELL_SIDEBAR_PLATFORM!r}."
    )


def assert_dataset_preview_visible(app: AppTest) -> None:
    """Assert dataset preview is available (expanded subheader or collapsed expander)."""
    from tests.app.golden_expectations import SECTION_DATASET_PREVIEW

    if find_expander(app, "Dataset Preview") is not None:
        assert_expander_present(app, "Dataset Preview")
        return

    assert_section_visible(app, SECTION_DATASET_PREVIEW)


def assert_profile_summary_visible(app: AppTest) -> None:
    from tests.app.golden_expectations import PROFILE_SUMMARY_HEADING

    sidebar = sidebar_visible_text(app)
    assert PROFILE_SUMMARY_HEADING in sidebar, (
        f"Expected {PROFILE_SUMMARY_HEADING!r} in sidebar."
    )
    assert "Rows" in sidebar, "Expected Rows profile indicator in sidebar."
    assert "Columns" in sidebar, "Expected Columns profile indicator in sidebar."


def assert_load_success_visible(app: AppTest) -> None:
    from tests.app.golden_expectations import LOAD_SUCCESS_MARKER

    assert LOAD_SUCCESS_MARKER in sidebar_visible_text(app)


def assert_sidebar_error_contains(app: AppTest, marker: str) -> None:
    sidebar = sidebar_visible_text(app).lower()
    assert marker.lower() in sidebar, (
        f"Expected sidebar error marker {marker!r}. Sidebar text: {sidebar_visible_text(app)!r}"
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
        app.sidebar.file_uploader[0].upload(upload_name, handle.read()).run()
    assert_no_app_exception(app)
    assert_dataset_loaded(app)
    assert_load_success_visible(app)
    return app


def attempt_invalid_upload(app: AppTest, csv_path: Path, *, filename: str | None = None) -> AppTest:
    """Upload a CSV without asserting that a dataset was loaded."""
    upload_name = filename or csv_path.name
    with csv_path.open("rb") as handle:
        app.sidebar.file_uploader[0].upload(upload_name, handle.read()).run()
    assert_no_app_exception(app)
    return app


def replace_sample_dataset(app: AppTest, sample_label: str) -> AppTest:
    """Load a different sidebar sample dataset, replacing the active dataset."""
    return load_sample_dataset(app, sample_label)


def ask_question(app: AppTest, question: str) -> AppTest:
    """Enter a natural-language question."""
    _seed_stale_clarification_widget_state(app)
    app.text_area(key="question").input(question).run()
    return app


def _seed_stale_clarification_widget_state(app: AppTest) -> None:
    """Seed resolved clarification widget keys retained by AppTest between runs."""
    for radio in app.radio:
        if radio.key and radio.key.startswith("clarification_"):
            if radio.key not in app.session_state and radio.options:
                app.session_state[radio.key] = radio.options[0]


def run_analysis(app: AppTest) -> AppTest:
    """Submit the current question for analysis."""
    analyze = app.button(key="analyze_question")
    assert not analyze.disabled, "Analyse button is disabled — enter a question first."
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


def assert_section_order(app: AppTest, *section_titles: str) -> None:
    """Assert section headings appear in the given order within visible text."""
    visible = user_visible_text(app)
    last_index = -1
    for title in section_titles:
        index = visible.index(title)
        assert index > last_index, (
            f"Expected {title!r} after prior sections. Order check failed for: {section_titles!r}"
        )
        last_index = index


def assert_analysis_header_visible(app: AppTest) -> None:
    """Assert the analysis header is shown with question and dataset context."""
    from tests.app.golden_expectations import ANALYSIS_HEADER_STATUS

    assert_results_visible(app)
    visible = user_visible_text(app)
    assert ANALYSIS_HEADER_STATUS in visible
    assert "Question" in visible
    assert "Dataset" in visible
    assert "Completed" in visible


def markdown_section_headings(app: AppTest) -> list[str]:
    """Return #### section headings in render order from markdown elements."""
    headings: list[str] = []
    prefix = "#### "
    for element in app.markdown:
        value = element.value or ""
        if value.startswith(prefix):
            headings.append(value[len(prefix) :].strip())
    return headings


def markdown_section_headings_from_text(text: str) -> list[str]:
    """Return #### section headings in order from aggregated markdown text."""
    headings: list[str] = []
    prefix = "#### "
    for line in text.splitlines():
        if line.startswith(prefix):
            headings.append(line[len(prefix) :].strip())
    return headings


def find_expander(app: AppTest, label: str):
    """Return the first expander matching the label, if present."""
    return next((item for item in app.expander if item.label == label), None)


def find_results_tab(app: AppTest, label: str):
    """Return the first results tab matching the label, if present."""
    return next((tab for tab in app.tabs if tab.label == label), None)


def assert_results_tabs_present(app: AppTest) -> None:
    """Assert the three Milestone 13d results tabs are present."""
    from ui.results_headings import TAB_AUDIT_LABEL, TAB_FINDINGS_LABEL, TAB_SUMMARY_LABEL

    labels = {tab.label for tab in app.tabs}
    assert TAB_SUMMARY_LABEL in labels, f"Expected Summary tab. Found: {labels!r}"
    assert TAB_FINDINGS_LABEL in labels, f"Expected Findings tab. Found: {labels!r}"
    assert TAB_AUDIT_LABEL in labels, f"Expected Audit tab. Found: {labels!r}"


def select_results_tab(app: AppTest, label: str) -> AppTest:
    """Verify a results tab exists (content is scoped to tab blocks in AppTest)."""
    tab = find_results_tab(app, label)
    assert tab is not None, f"Expected results tab {label!r} to be present."
    return app


def _summary_tab(app: AppTest):
    from ui.results_headings import TAB_SUMMARY_LABEL

    tab = find_results_tab(app, TAB_SUMMARY_LABEL)
    assert tab is not None, f"Expected {TAB_SUMMARY_LABEL!r} tab."
    return tab


def _findings_tab(app: AppTest):
    from ui.results_headings import TAB_FINDINGS_LABEL

    tab = find_results_tab(app, TAB_FINDINGS_LABEL)
    assert tab is not None, f"Expected {TAB_FINDINGS_LABEL!r} tab."
    return tab


def _audit_tab(app: AppTest):
    from ui.results_headings import TAB_AUDIT_LABEL

    tab = find_results_tab(app, TAB_AUDIT_LABEL)
    assert tab is not None, f"Expected {TAB_AUDIT_LABEL!r} tab."
    return tab


def expand_disclosure(app: AppTest, label: str) -> AppTest:
    """Verify a disclosure group exists (AppTest renders expander content in the tree)."""
    expander = find_expander(app, label)
    assert expander is not None, f"Expected expander {label!r} to be present."
    return app


def assert_expander_present(app: AppTest, label: str, *, expanded: bool | None = None) -> None:
    expander = find_expander(app, label)
    assert expander is not None, f"Expected expander {label!r} to be present."
    if expanded is not None:
        assert expander.proto.expanded is expanded, (
            f"Expected expander {label!r} expanded={expanded}, got {expander.proto.expanded}"
        )


def assert_executive_surface_visible(app: AppTest) -> None:
    """Assert Summary tab content is visible by default (Executive Surface)."""
    assert_summary_tab_visible(app)


def assert_summary_tab_visible(app: AppTest) -> None:
    """Assert default Summary tab content is present and scoped correctly."""
    from src.operational_intelligence.llm.narrative_governance import (
        ADVISOR_SECTION_EXECUTIVE_ACTIONS,
        ADVISOR_SECTION_KEY_MESSAGE,
    )
    from tests.app.golden_expectations import (
        ANALYTICAL_FINDINGS_HEADING,
        ANALYSIS_HEADER_STATUS,
        SECTION_DIRECT_ANSWER,
        SECTION_EXECUTIVE_SUMMARY,
        SECTION_SYSTEM_TRANSPARENCY,
    )
    from ui.narrative_presentation import (
        ASSESSMENT_CONFIDENCE_HEADING,
        EXECUTIVE_ASSESSMENT_HEADING,
        GENERATED_BY_HEADING,
    )

    assert_results_tabs_present(app)
    assert_analysis_header_visible(app)

    summary_text = tab_user_visible_text(_summary_tab(app))
    findings_text = tab_user_visible_text(_findings_tab(app))
    audit_text = tab_user_visible_text(_audit_tab(app))
    summary_headings = markdown_section_headings_from_text(summary_text)
    findings_headings = markdown_section_headings_from_text(findings_text)
    audit_headings = markdown_section_headings_from_text(audit_text)

    assert ANALYSIS_HEADER_STATUS in user_visible_text(app)
    assert EXECUTIVE_ASSESSMENT_HEADING in summary_text
    assert ADVISOR_SECTION_KEY_MESSAGE in summary_text
    assert ADVISOR_SECTION_EXECUTIVE_ACTIONS in summary_text
    assert ASSESSMENT_CONFIDENCE_HEADING in summary_text

    assert SECTION_DIRECT_ANSWER in summary_headings
    assert SECTION_EXECUTIVE_SUMMARY in summary_headings
    assert ANALYTICAL_FINDINGS_HEADING not in summary_headings
    assert SECTION_SYSTEM_TRANSPARENCY not in summary_headings
    assert GENERATED_BY_HEADING not in summary_text
    assert SECTION_DIRECT_ANSWER not in findings_headings
    assert SECTION_DIRECT_ANSWER not in audit_headings


def assert_investigation_collapsed_by_default(app: AppTest) -> None:
    """Legacy alias: Findings content is not on the default Summary tab."""
    assert_findings_tab_not_on_summary(app)


def assert_findings_tab_not_on_summary(app: AppTest) -> None:
    from tests.app.golden_expectations import ANALYTICAL_FINDINGS_HEADING

    assert_results_tabs_present(app)
    summary_headings = markdown_section_headings_from_text(
        tab_user_visible_text(_summary_tab(app))
    )
    assert ANALYTICAL_FINDINGS_HEADING not in summary_headings


def assert_audit_collapsed_by_default(app: AppTest) -> None:
    """Legacy alias: Audit content is not on the default Summary tab."""
    assert_audit_tab_not_on_summary(app)


def assert_audit_tab_not_on_summary(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_SYSTEM_TRANSPARENCY
    from ui.narrative_presentation import GENERATED_BY_HEADING

    assert_results_tabs_present(app)
    summary_headings = markdown_section_headings_from_text(
        tab_user_visible_text(_summary_tab(app))
    )
    assert SECTION_SYSTEM_TRANSPARENCY not in summary_headings
    assert GENERATED_BY_HEADING not in tab_user_visible_text(_summary_tab(app))


def expand_investigation_disclosure(app: AppTest) -> AppTest:
    """Legacy alias: verify Findings tab exists for tab-scoped assertions."""
    from ui.results_headings import TAB_FINDINGS_LABEL

    return select_results_tab(app, TAB_FINDINGS_LABEL)


def expand_audit_disclosure(app: AppTest) -> AppTest:
    """Legacy alias: verify Audit tab exists for tab-scoped assertions."""
    from ui.results_headings import TAB_AUDIT_LABEL

    return select_results_tab(app, TAB_AUDIT_LABEL)


def assert_investigation_reachable(app: AppTest) -> None:
    from tests.app.golden_expectations import ANALYTICAL_FINDINGS_HEADING
    from ui.results_headings import TAB_FINDINGS_LABEL

    select_results_tab(app, TAB_FINDINGS_LABEL)
    findings_text = tab_user_visible_text(_findings_tab(app))
    assert ANALYTICAL_FINDINGS_HEADING in findings_text
    assert_executive_reasoning(app)


def assert_findings_reachable(app: AppTest) -> None:
    assert_investigation_reachable(app)


def assert_audit_reachable(app: AppTest) -> None:
    from ui.narrative_presentation import GENERATED_BY_HEADING, GOVERNANCE_CAPTION
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    audit_text = tab_user_visible_text(_audit_tab(app))
    assert "Routed tools:" in audit_text
    assert GENERATED_BY_HEADING in audit_text
    assert GOVERNANCE_CAPTION in audit_text


def assert_results_information_architecture(app: AppTest) -> None:
    """Assert Milestone 13b hierarchy within tab-scoped results content."""
    from tests.app.golden_expectations import (
        ANALYSIS_HEADER_STATUS,
        ANALYTICAL_FINDINGS_HEADING,
        SECTION_DIRECT_ANSWER,
        SECTION_EXECUTIVE_SUMMARY,
        SECTION_SYSTEM_TRANSPARENCY,
    )
    from ui.executive_reasoning_presentation import EXECUTIVE_REASONING_HEADING
    from ui.narrative_presentation import GENERATED_BY_HEADING
    from ui.results_headings import TAB_AUDIT_LABEL, TAB_FINDINGS_LABEL

    assert_summary_tab_visible(app)
    select_results_tab(app, TAB_FINDINGS_LABEL)
    select_results_tab(app, TAB_AUDIT_LABEL)

    summary_text = tab_user_visible_text(_summary_tab(app))
    findings_text = tab_user_visible_text(_findings_tab(app))
    audit_text = tab_user_visible_text(_audit_tab(app))
    visible = user_visible_text(app)

    assert visible.index(ANALYSIS_HEADER_STATUS) < visible.index(SECTION_DIRECT_ANSWER)
    assert summary_text.index(SECTION_DIRECT_ANSWER) < summary_text.index(SECTION_EXECUTIVE_SUMMARY)

    findings_headings = markdown_section_headings_from_text(findings_text)
    assert ANALYTICAL_FINDINGS_HEADING in findings_headings
    if EXECUTIVE_REASONING_HEADING in findings_headings:
        assert findings_headings.index(ANALYTICAL_FINDINGS_HEADING) < findings_headings.index(
            EXECUTIVE_REASONING_HEADING
        )

    assert SECTION_SYSTEM_TRANSPARENCY in audit_text
    assert "Verification" in audit_text
    assert GENERATED_BY_HEADING in audit_text


def assert_results_visible(app: AppTest) -> None:
    """Assert the results panel is shown."""
    assert_section_visible(app, SECTION_RESULTS)
    blocking_errors = [
        item.value
        for item in app.error
        if item.value
        and "uploaded CSV is empty" not in item.value
        and "Could not read CSV" not in item.value
    ]
    assert not blocking_errors, f"Unexpected app error: {blocking_errors}"


def assert_direct_answer(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_DIRECT_ANSWER

    assert_results_visible(app)
    assert_section_visible(app, SECTION_DIRECT_ANSWER)


def assert_operational_assessment(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_OPERATIONAL_ASSESSMENT
    from ui.results_headings import TAB_FINDINGS_LABEL

    select_results_tab(app, TAB_FINDINGS_LABEL)
    assert SECTION_OPERATIONAL_ASSESSMENT in tab_user_visible_text(_findings_tab(app))


def assert_executive_reasoning(app: AppTest) -> None:
    from tests.app.golden_expectations import EXECUTIVE_REASONING_HEADING
    from ui.results_headings import TAB_FINDINGS_LABEL

    select_results_tab(app, TAB_FINDINGS_LABEL)
    assert EXECUTIVE_REASONING_HEADING in tab_user_visible_text(_findings_tab(app))


def assert_executive_conclusions(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_EXECUTIVE_CONCLUSIONS
    from ui.results_headings import TAB_FINDINGS_LABEL

    select_results_tab(app, TAB_FINDINGS_LABEL)
    assert SECTION_EXECUTIVE_CONCLUSIONS in tab_user_visible_text(_findings_tab(app))


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
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    assert SNAPSHOT_TRANSPARENCY_MARKER in tab_user_visible_text(_audit_tab(app))


def assert_temporal_filter_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import TEMPORAL_FILTER_MARKER
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    assert TEMPORAL_FILTER_MARKER in tab_user_visible_text(_audit_tab(app))


def assert_snapshot_not_active(app: AppTest) -> None:
    from tests.app.golden_expectations import SNAPSHOT_TRANSPARENCY_MARKER

    assert SNAPSHOT_TRANSPARENCY_MARKER not in user_visible_text(app)


def assert_snapshot_contributors_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import SNAPSHOT_CONTRIBUTORS_MARKER
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    visible = tab_user_visible_text(_audit_tab(app))
    assert SNAPSHOT_CONTRIBUTORS_MARKER in visible
    assert "Dimension:" in visible
    assert "Highest:" in visible
    assert "Lowest:" in visible


def assert_priority_actions(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_PRIORITY_ACTIONS
    from ui.results_headings import TAB_FINDINGS_LABEL

    select_results_tab(app, TAB_FINDINGS_LABEL)
    assert SECTION_PRIORITY_ACTIONS in tab_user_visible_text(_findings_tab(app))


def assert_transparency(app: AppTest) -> None:
    from tests.app.golden_expectations import SECTION_SYSTEM_TRANSPARENCY
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    assert SECTION_SYSTEM_TRANSPARENCY in tab_user_visible_text(_audit_tab(app))


def assert_narrative_placeholder_visible(app: AppTest) -> None:
    from tests.app.golden_expectations import (
        NARRATIVE_DISABLED_MARKER,
        SECTION_AI_ASSISTED_EXECUTIVE_NARRATIVE,
    )
    from ui.results_headings import TAB_SUMMARY_LABEL

    assert_section_visible(app, SECTION_AI_ASSISTED_EXECUTIVE_NARRATIVE)
    select_results_tab(app, TAB_SUMMARY_LABEL)
    visible = tab_user_visible_text(_summary_tab(app))
    assert NARRATIVE_DISABLED_MARKER in visible, (
        "Expected disabled narrative placeholder message on the Summary tab."
    )


def assert_narrative_placeholder_hidden(app: AppTest) -> None:
    from tests.app.golden_expectations import NARRATIVE_DISABLED_MARKER
    from ui.results_headings import TAB_SUMMARY_LABEL

    select_results_tab(app, TAB_SUMMARY_LABEL)
    visible = tab_user_visible_text(_summary_tab(app))
    assert NARRATIVE_DISABLED_MARKER not in visible, (
        "Placeholder should not appear when narrative is enabled."
    )


def select_narrative_mode(app: AppTest, mode: str) -> AppTest:
    """Select a sidebar narrative mode using internal mode values."""
    app.sidebar.radio(key="narrative_mode").set_value(mode).run()
    return app


def assert_provider_status_visible(app: AppTest, marker: str) -> None:
    """Assert provider status text is visible in the sidebar."""
    sidebar = sidebar_visible_text(app)
    assert marker in sidebar, f"Expected provider status marker {marker!r} in sidebar."


def assert_generation_method_visible(app: AppTest, marker: str) -> None:
    """Assert backend-driven generation method text is visible in results."""
    from ui.results_headings import TAB_AUDIT_LABEL

    select_results_tab(app, TAB_AUDIT_LABEL)
    visible = tab_user_visible_text(_audit_tab(app))
    assert marker in visible, f"Expected generation method marker {marker!r} in visible text."


def assert_narrative_content_reachable(app: AppTest) -> None:
    from src.operational_intelligence.llm.narrative_governance import ADVISOR_SECTION_TITLES
    from ui.narrative_presentation import (
        ASSESSMENT_CONFIDENCE_HEADING,
        EXECUTIVE_ASSESSMENT_HEADING,
        LIMITATIONS_HEADING,
    )
    from ui.results_headings import TAB_AUDIT_LABEL, TAB_FINDINGS_LABEL

    assert_summary_tab_visible(app)
    select_results_tab(app, TAB_FINDINGS_LABEL)
    select_results_tab(app, TAB_AUDIT_LABEL)

    summary_text = tab_user_visible_text(_summary_tab(app))
    findings_text = tab_user_visible_text(_findings_tab(app))
    audit_text = tab_user_visible_text(_audit_tab(app))
    expander_labels = {expander.label for expander in app.expander}

    assert EXECUTIVE_ASSESSMENT_HEADING in summary_text
    assert ASSESSMENT_CONFIDENCE_HEADING in summary_text

    for heading in ADVISOR_SECTION_TITLES:
        in_summary = heading in summary_text or heading in expander_labels
        in_findings = heading in findings_text
        assert in_summary or in_findings, (
            f"Expected narrative heading {heading!r} to be reachable."
        )

    assert LIMITATIONS_HEADING in expander_labels or LIMITATIONS_HEADING in summary_text
    from ui.narrative_presentation import GOVERNANCE_CAPTION

    assert GOVERNANCE_CAPTION in audit_text


def assert_narrative_content_visible(app: AppTest) -> None:
    assert_narrative_content_reachable(app)


def assert_expected_sections(app: AppTest, sections: tuple[str, ...]) -> None:
    """Assert all expected user-visible sections are present across results tabs."""
    visible = results_tabs_visible_text(app)
    for section in sections:
        assert section in visible, f"Expected section {section!r} across results tabs."


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


def _final_golden_question(scenario: GoldenScenario) -> GoldenQuestion:
    if scenario.replacement_question is not None:
        return scenario.replacement_question
    if scenario.follow_up_question is not None:
        return scenario.follow_up_question
    return scenario.question


def assert_journey_outcome(app: AppTest, scenario_id: str) -> None:
    """Assert the registered behavioural outcome for a golden user journey."""
    scenario = get_scenario(scenario_id)
    question = _final_golden_question(scenario)

    assert_no_app_exception(app)

    if scenario_id == "dataset_onboarding_journey":
        assert_bootstrap_prompt_hidden(app)
        assert_dataset_preview_visible(app)
        assert_profile_summary_visible(app)

    if scenario.invalid_fixture_path is not None:
        assert_sidebar_error_contains(app, scenario.invalid_error_marker)
        assert_dataset_preview_visible(app)

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

    if scenario.replacement_dataset is not None:
        assert scenario.replacement_dataset.sidebar_label is not None
        replace_sample_dataset(app, scenario.replacement_dataset.sidebar_label)
        assert_section_hidden(app, SECTION_RESULTS)
        assert_dataset_preview_visible(app)
        assert_profile_summary_visible(app)
        if scenario.replacement_question is not None:
            execute_golden_question(app, scenario.replacement_question)

    if scenario.invalid_fixture_path is not None:
        attempt_invalid_upload(app, scenario.invalid_fixture_path)
        execute_golden_question(app, scenario.question)

    if scenario.follow_up_question is not None:
        run_follow_up_question(app, scenario.follow_up_question)

    return app
