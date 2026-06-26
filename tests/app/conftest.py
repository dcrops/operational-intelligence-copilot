"""Fixtures for Streamlit application tests."""

from __future__ import annotations

import pytest

from tests.app.helpers import launch_app


@pytest.fixture(autouse=True)
def _clear_narrative_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent narrative environment variables leaking between AppTests."""
    monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
    monkeypatch.delenv("OIC_NARRATIVE_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def app():
    """Fresh Streamlit AppTest instance at bootstrap (no dataset loaded)."""
    return launch_app()
