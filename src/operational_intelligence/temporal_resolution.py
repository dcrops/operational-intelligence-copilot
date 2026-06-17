"""Deterministic temporal constraint parsing and DataFrame filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

import pandas as pd

_MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_MONTH_PATTERN = (
    r"(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)"
)

_OUT_OF_SCOPE_PATTERNS = (
    re.compile(r"\bthis\s+month\b", re.IGNORECASE),
    re.compile(r"\blast\s+month\b", re.IGNORECASE),
    re.compile(r"\bcompare\b", re.IGNORECASE),
    re.compile(r"\bsince\b", re.IGNORECASE),
    re.compile(r"\bafter\b", re.IGNORECASE),
)

_QUARTER_YEAR_PATTERN = re.compile(
    rf"(?:\bq([1-4])\b|\bquarter\s+([1-4])\b)\s+(20\d{{2}})\b",
    re.IGNORECASE,
)

_MONTH_YEAR_PATTERN = re.compile(
    rf"\b({_MONTH_PATTERN})\s+(20\d{{2}})\b",
    re.IGNORECASE,
)

_YEAR_ONLY_PATTERN = re.compile(
    r"\b(?:in\s+)?(20\d{2})\b",
    re.IGNORECASE,
)

_MONTH_ONLY_PATTERN = re.compile(
    rf"\b(?:in\s+)?({_MONTH_PATTERN})\b(?!\s+20\d{{2}})",
    re.IGNORECASE,
)


class TemporalConstraintKind(str, Enum):
    MONTH_YEAR = "month_year"
    MONTH_ONLY = "month_only"
    YEAR = "year"
    QUARTER = "quarter"


@dataclass(frozen=True)
class TemporalConstraint:
    """A resolved explicit temporal period from a user question."""

    label: str
    kind: TemporalConstraintKind
    start: pd.Timestamp | None = None
    end: pd.Timestamp | None = None
    calendar_month: int | None = None


def _month_number(name: str) -> int:
    return _MONTH_NAMES[name.lower()]


def _month_name(month: int) -> str:
    for name, number in _MONTH_NAMES.items():
        if number == month:
            return name.capitalize()
    raise ValueError(f"Invalid month number: {month}")


def _quarter_bounds(quarter: int, year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    if quarter not in {1, 2, 3, 4}:
        raise ValueError(f"Invalid quarter: {quarter}")

    start_month = ((quarter - 1) * 3) + 1
    start = pd.Timestamp(year=year, month=start_month, day=1)
    if quarter == 4:
        end = pd.Timestamp(year=year + 1, month=1, day=1)
    else:
        end = pd.Timestamp(year=year, month=start_month + 3, day=1)
    return start, end


def _is_out_of_scope(question: str) -> bool:
    return any(pattern.search(question) for pattern in _OUT_OF_SCOPE_PATTERNS)


def parse_temporal_constraint(question: str) -> TemporalConstraint | None:
    """Parse an explicit temporal period from a natural language question."""
    if not isinstance(question, str) or not question.strip():
        return None

    if _is_out_of_scope(question):
        return None

    quarter_match = _QUARTER_YEAR_PATTERN.search(question)
    if quarter_match:
        quarter = int(quarter_match.group(1) or quarter_match.group(2))
        year = int(quarter_match.group(3))
        start, end = _quarter_bounds(quarter, year)
        return TemporalConstraint(
            label=f"Q{quarter} {year}",
            kind=TemporalConstraintKind.QUARTER,
            start=start,
            end=end,
        )

    month_year_match = _MONTH_YEAR_PATTERN.search(question)
    if month_year_match:
        month_name = month_year_match.group(1)
        year = int(month_year_match.group(2))
        month = _month_number(month_name)
        start = pd.Timestamp(year=year, month=month, day=1)
        if month == 12:
            end = pd.Timestamp(year=year + 1, month=1, day=1)
        else:
            end = pd.Timestamp(year=year, month=month + 1, day=1)
        return TemporalConstraint(
            label=f"{_month_name(month)} {year}",
            kind=TemporalConstraintKind.MONTH_YEAR,
            start=start,
            end=end,
        )

    year_matches = list(_YEAR_ONLY_PATTERN.finditer(question))
    if year_matches:
        # Prefer the last explicit year mention when multiple exist, unless a month+year
        # or quarter already matched above.
        year = int(year_matches[-1].group(1))
        start = pd.Timestamp(year=year, month=1, day=1)
        end = pd.Timestamp(year=year + 1, month=1, day=1)
        return TemporalConstraint(
            label=str(year),
            kind=TemporalConstraintKind.YEAR,
            start=start,
            end=end,
        )

    month_only_match = _MONTH_ONLY_PATTERN.search(question)
    if month_only_match:
        month = _month_number(month_only_match.group(1))
        return TemporalConstraint(
            label=_month_name(month),
            kind=TemporalConstraintKind.MONTH_ONLY,
            calendar_month=month,
        )

    return None


def _parse_date_column(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def apply_temporal_filter(
    df: pd.DataFrame,
    date_column: str,
    constraint: TemporalConstraint,
) -> pd.DataFrame:
    """Return rows from df whose date_column values fall within the constraint."""
    if date_column not in df.columns:
        raise ValueError(f"date_column '{date_column}' not found in DataFrame")

    parsed_dates = _parse_date_column(df[date_column])
    valid = parsed_dates.notna()
    if not valid.any():
        return df.iloc[0:0].copy()

    if constraint.kind == TemporalConstraintKind.MONTH_ONLY:
        if constraint.calendar_month is None:
            raise ValueError("MONTH_ONLY constraints require calendar_month")
        mask = valid & (parsed_dates.dt.month == constraint.calendar_month)
        return df.loc[mask].copy()

    if constraint.start is None or constraint.end is None:
        raise ValueError(f"{constraint.kind} constraints require start and end bounds")

    mask = valid & (parsed_dates >= constraint.start) & (parsed_dates < constraint.end)
    return df.loc[mask].copy()
