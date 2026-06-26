"""Application bootstrap and smoke tests (Milestone 10c)."""

from __future__ import annotations

import pytest

from tests.app.golden_expectations import (
    EXECUTIVE_REASONING_SECTIONS,
    SECTION_SYSTEM_TRANSPARENCY,
    STANDARD_RESULTS_SECTIONS,
    get_scenario,
)
from tests.app.helpers import (
    assert_app_shell_visible,
    assert_bootstrap_prompt_visible,
    assert_expected_sections,
    assert_no_app_exception,
    assert_results_visible,
    load_sample_dataset,
    run_golden_scenario,
)

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


class TestApplicationMarkers:
    def test_app_markers_registered(self, pytestconfig):
        raw = pytestconfig.getini("markers")
        if isinstance(raw, str):
            lines = raw.splitlines()
        else:
            lines = raw
        marker_names = {line.split(":")[0].strip() for line in lines if line.strip()}
        assert {"app", "streamlit", "ui"}.issubset(marker_names)


class TestApplicationBootstrap:
    def test_app_launches_without_dataset(self, app):
        assert_no_app_exception(app)
        assert_app_shell_visible(app)
        assert_bootstrap_prompt_visible(app)

    def test_manufacturing_sample_loads_from_sidebar(self, app):
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        assert_no_app_exception(app)
        assert app.session_state["dataset_name"] == scenario.dataset.app_dataset_name
        assert app.session_state["profile"] is not None
        assert any(subheader.value == "Dataset Preview" for subheader in app.subheader)


class TestManufacturingBootstrapSmoke:
    """Single application smoke test for Milestone 10c."""

    def test_manufacturing_executive_report_sections_render(self, app):
        run_golden_scenario(app, "manufacturing_bootstrap_smoke")

        assert_results_visible(app)
        assert_expected_sections(
            app,
            (
                *STANDARD_RESULTS_SECTIONS,
                *EXECUTIVE_REASONING_SECTIONS,
                SECTION_SYSTEM_TRANSPARENCY,
            ),
        )
