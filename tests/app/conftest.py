"""Fixtures for Streamlit application tests."""

from __future__ import annotations

import pytest

from tests.app.helpers import launch_app


@pytest.fixture
def app():
    """Fresh Streamlit AppTest instance at bootstrap (no dataset loaded)."""
    return launch_app()
