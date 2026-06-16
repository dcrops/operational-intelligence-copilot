"""Synthetic domain DataFrames and profiles for deterministic tests."""

from __future__ import annotations

import pandas as pd

from src.operational_intelligence.models import DatasetProfile
from src.operational_intelligence.profiling import DatasetProfiler

# Known expected outcomes for the default synthetic datasets below.
MANUFACTURING_HIGHEST_DEFECTS_LINE = "Line B"
MANUFACTURING_LOWEST_DOWNTIME_LINE = "Line A"
EDUCATION_LOWEST_ATTENDANCE_SCHOOL = "School B"
WORKFORCE_HIGHEST_HOURS_DEPARTMENT = "Ops"
WORKFORCE_LOWEST_HOURS_DEPARTMENT = "HR"


def make_manufacturing_df() -> pd.DataFrame:
    """
    Small manufacturing dataset with date, dimensions, and three metrics.

    Line B has higher defects; Line A has lower downtime. One row includes a
    units_produced spike suitable for anomaly detection.
    """
    dates = pd.date_range("2026-01-01", periods=4, freq="MS")
    rows: list[dict] = []
    for month in dates:
        rows.append(
            {
                "month": month,
                "production_line": "Line A",
                "shift": "Day",
                "defects": 2,
                "downtime_minutes": 20,
                "units_produced": 1000,
                "site": "North Plant",
                "supervisor": "Taylor",
            }
        )
        rows.append(
            {
                "month": month,
                "production_line": "Line B",
                "shift": "Day",
                "defects": 8,
                "downtime_minutes": 45,
                "units_produced": 500,
                "site": "South Plant",
                "supervisor": "Drew",
            }
        )

    df = pd.DataFrame(rows)
    # Single spike for anomaly detection scenarios.
    df.loc[df.index[-1], "units_produced"] = 5000
    return df


def make_education_df() -> pd.DataFrame:
    """
    Small education dataset with attendance_rate (mean aggregation) and
    multiple metrics/dimensions for clarification scenarios.
    """
    dates = pd.date_range("2026-01-01", periods=3, freq="MS")
    rows: list[dict] = []
    for index, month in enumerate(dates):
        rows.append(
            {
                "month": month,
                "school": "School A",
                "year_level": "Year 7",
                "attendance_rate": 90.0,
                "behaviour_incidents": 1,
                "average_score": 85.0,
                "campus": "Main",
                "program_type": "Mainstream",
            }
        )
        rows.append(
            {
                "month": month,
                "school": "School B",
                "year_level": "Year 8",
                "attendance_rate": 70.0 + index,
                "behaviour_incidents": 2,
                "average_score": 75.0,
                "campus": "East",
                "program_type": "Support",
            }
        )
    return pd.DataFrame(rows)


def make_workforce_df() -> pd.DataFrame:
    """
    Small workforce dataset with departments, multiple metrics, and time series.
    """
    dates = pd.date_range("2026-01-01", periods=3, freq="MS")
    rows: list[dict] = []
    for month in dates:
        rows.append(
            {
                "employee_id": "E001",
                "employee_name": "Alex Nguyen",
                "department": WORKFORCE_HIGHEST_HOURS_DEPARTMENT,
                "month": month,
                "hours": 200.0,
                "overtime_hours": 5.0,
                "absence_days": 1,
                "location": "Melbourne",
                "manager": "Michael",
                "employment_type": "Full Time",
            }
        )
        rows.append(
            {
                "employee_id": "E002",
                "employee_name": "Sam Lee",
                "department": WORKFORCE_LOWEST_HOURS_DEPARTMENT,
                "month": month,
                "hours": 160.0,
                "overtime_hours": 2.0,
                "absence_days": 0,
                "location": "Sydney",
                "manager": "Sarah",
                "employment_type": "Full Time",
            }
        )
    return pd.DataFrame(rows)


def make_profile(dataset_name: str, df: pd.DataFrame) -> DatasetProfile:
    """Profile a synthetic DataFrame for pipeline and ambiguity tests."""
    return DatasetProfiler().profile_dataframe(dataset_name, df)


def manufacturing_bundle() -> tuple[pd.DataFrame, DatasetProfile]:
    df = make_manufacturing_df()
    return df, make_profile("manufacturing_synthetic", df)


def education_bundle() -> tuple[pd.DataFrame, DatasetProfile]:
    df = make_education_df()
    return df, make_profile("education_synthetic", df)


def workforce_bundle() -> tuple[pd.DataFrame, DatasetProfile]:
    df = make_workforce_df()
    return df, make_profile("workforce_synthetic", df)
