"""Shared fixtures for Operational Intelligence Copilot regression tests."""

from __future__ import annotations

import pandas as pd
import pytest

from src.operational_intelligence.models import AnalysisRequest, DatasetProfile
from src.operational_intelligence.profiling import DatasetProfiler

MANUFACTURING_METRICS = ["defects", "downtime_minutes", "units_produced"]
MANUFACTURING_DIMENSIONS = [
    "production_line",
    "shift",
    "site",
    "supervisor",
]
WORKFORCE_METRICS = ["hours", "overtime_hours", "absence_days"]
WORKFORCE_DIMENSIONS = [
    "employee_id",
    "employee_name",
    "department",
    "location",
    "manager",
    "employment_type",
]


@pytest.fixture
def manufacturing_df() -> pd.DataFrame:
    return pd.read_csv("data/sample/manufacturing_demo.csv")


@pytest.fixture
def manufacturing_profile(manufacturing_df: pd.DataFrame) -> DatasetProfile:
    return DatasetProfiler().profile_dataframe("manufacturing_demo", manufacturing_df)


@pytest.fixture
def workforce_df() -> pd.DataFrame:
    return pd.read_csv("data/sample/workforce_demo_v2.csv")


@pytest.fixture
def workforce_profile(workforce_df: pd.DataFrame) -> DatasetProfile:
    return DatasetProfiler().profile_dataframe("workforce_demo_v2", workforce_df)


@pytest.fixture
def manufacturing_trend_request() -> AnalysisRequest:
    return AnalysisRequest(
        question="How has downtime_minutes changed over time?",
        dataset_names=["manufacturing_demo"],
    )


@pytest.fixture
def manufacturing_variance_request() -> AnalysisRequest:
    return AnalysisRequest(
        question="Which production line has the highest defects?",
        dataset_names=["manufacturing_demo"],
    )


@pytest.fixture
def workforce_variance_request() -> AnalysisRequest:
    return AnalysisRequest(
        question="Which department has the highest hours?",
        dataset_names=["workforce_demo_v2"],
    )
