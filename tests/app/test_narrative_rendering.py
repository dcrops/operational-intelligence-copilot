"""AppTests for Milestone 11d — Executive Narrative Rendering."""

from __future__ import annotations

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import GENERATOR_TYPE
from tests.app.golden_expectations import get_scenario
from tests.app.helpers import (
    assert_direct_answer,
    assert_executive_reasoning,
    assert_narrative_content_visible,
    assert_narrative_placeholder_hidden,
    assert_narrative_placeholder_visible,
    assert_transparency,
    ask_question,
    launch_app,
    load_sample_dataset,
    run_analysis,
    user_visible_text,
)

pytestmark = [pytest.mark.app, pytest.mark.streamlit, pytest.mark.ui]


def _clear_narrative_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
    monkeypatch.delenv("OIC_NARRATIVE_PROVIDER", raising=False)


def _enable_deterministic_narrative_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
    monkeypatch.setenv("OIC_NARRATIVE_PROVIDER", "deterministic")


class TestNarrativeRenderingDisabled:
    def test_placeholder_shown_when_narrative_disabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _clear_narrative_env(monkeypatch)

        app = launch_app()
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_narrative_placeholder_visible(app)
        assert_direct_answer(app)


class TestNarrativeRenderingEnabled:
    def test_deterministic_provider_renders_narrative_without_placeholder(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _enable_deterministic_narrative_env(monkeypatch)

        app = launch_app()
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_narrative_placeholder_hidden(app)
        assert_narrative_content_visible(app)
        assert f"Generator: {GENERATOR_TYPE}" in user_visible_text(app)

    def test_deterministic_sections_preserved_when_narrative_enabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _enable_deterministic_narrative_env(monkeypatch)

        app = launch_app()
        scenario = get_scenario("manufacturing_bootstrap_smoke")
        load_sample_dataset(app, scenario.dataset.sidebar_label)

        ask_question(app, scenario.question.question)
        run_analysis(app)

        assert_narrative_placeholder_hidden(app)
        assert_direct_answer(app)
        assert_executive_reasoning(app)
        assert_transparency(app)
        assert_narrative_content_visible(app)
