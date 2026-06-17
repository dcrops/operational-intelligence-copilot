"""Snapshot analysis for single-period scoped datasets."""

from __future__ import annotations

import pandas as pd

from src.operational_intelligence.evidence_utils import build_supporting_context
from src.operational_intelligence.models import (
    EvidenceItem,
    Finding,
    SnapshotContext,
    SnapshotContributor,
    ToolResult,
)
from src.operational_intelligence.question_semantics import (
    AggregationType,
    infer_aggregation_type,
)

SNAPSHOT_REASON = "Only one temporal period remained in the scoped dataset."
BASELINE_SCOPE = "full_dataset"
CONTRIBUTOR_HIGHEST = "highest"
CONTRIBUTOR_LOWEST = "lowest"


def _parse_date_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _format_date(value: object) -> str:
    if hasattr(value, "date"):
        return str(value.date())
    return str(value)


def count_distinct_temporal_buckets(df: pd.DataFrame, date_column: str) -> int:
    """Count distinct temporal buckets using the same parsing as TrendAnalysisTool."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return 0
    if date_column not in df.columns:
        raise ValueError(f"date_column '{date_column}' not found in DataFrame")

    parsed_dates = _parse_date_column(df[date_column])
    valid = parsed_dates.notna()
    if not valid.any():
        return 0

    return int(parsed_dates.loc[valid].nunique())


def _aggregate_by_period(
    df: pd.DataFrame,
    date_column: str,
    metric_column: str,
    aggregation: AggregationType,
) -> pd.Series:
    data = df[[date_column, metric_column]].copy()
    data[date_column] = _parse_date_column(data[date_column])
    data = data.dropna(subset=[date_column, metric_column])
    if data.empty:
        return pd.Series(dtype=float)

    grouped = data.groupby(date_column, dropna=False)[metric_column]
    if aggregation == "mean":
        aggregated = grouped.mean()
    else:
        aggregated = grouped.sum()
    return aggregated.sort_index()


def _aggregate_by_dimension(
    df: pd.DataFrame,
    dimension_column: str,
    metric_column: str,
    aggregation: AggregationType,
) -> pd.Series:
    data = df[[dimension_column, metric_column]].copy()
    data = data.dropna(subset=[dimension_column, metric_column])
    if data.empty:
        return pd.Series(dtype=float)

    grouped = data.groupby(dimension_column, dropna=False)[metric_column]
    if aggregation == "mean":
        aggregated = grouped.mean()
    else:
        aggregated = grouped.sum()
    return aggregated.sort_index()


def _pick_contributor_entity(aggregated: pd.Series, *, highest: bool) -> tuple[str, float] | None:
    if aggregated.empty:
        return None

    target_value = float(aggregated.max() if highest else aggregated.min())
    matches = aggregated[aggregated == target_value]
    entity_name = str(sorted(matches.index, key=str)[0])
    return entity_name, target_value


def resolve_snapshot_contributors(
    scoped_df: pd.DataFrame,
    dimension_column: str,
    metric_column: str,
    aggregation: AggregationType,
) -> tuple[SnapshotContributor, SnapshotContributor] | None:
    """Return highest and lowest contributors when dimension grouping is meaningful."""
    if dimension_column not in scoped_df.columns:
        return None
    if metric_column not in scoped_df.columns:
        return None

    aggregated = _aggregate_by_dimension(
        scoped_df,
        dimension_column,
        metric_column,
        aggregation,
    )
    if len(aggregated) < 2:
        return None

    highest = _pick_contributor_entity(aggregated, highest=True)
    lowest = _pick_contributor_entity(aggregated, highest=False)
    if highest is None or lowest is None:
        return None
    if highest[1] == lowest[1] and highest[0] == lowest[0]:
        return None

    return (
        SnapshotContributor(
            dimension_name=dimension_column,
            entity_name=highest[0],
            value=highest[1],
        ),
        SnapshotContributor(
            dimension_name=dimension_column,
            entity_name=lowest[0],
            value=lowest[1],
        ),
    )


def extract_snapshot_contributors(
    finding: Finding,
) -> tuple[str, SnapshotContributor, SnapshotContributor] | None:
    """Extract contributor metadata from snapshot finding evidence."""
    highest: SnapshotContributor | None = None
    lowest: SnapshotContributor | None = None
    dimension_name: str | None = None

    for item in finding.evidence:
        context = item.supporting_context
        if context.get("analysis_mode") != "snapshot":
            continue
        if context.get("is_snapshot_contributor") is not True:
            continue
        if not isinstance(item.metric_value, (int, float)):
            continue

        role = context.get("contributor_role")
        dimension = str(context.get("dimension_name") or "")
        entity = str(context.get("entity_name") or "")
        if not dimension or not entity or role not in {CONTRIBUTOR_HIGHEST, CONTRIBUTOR_LOWEST}:
            continue

        contributor = SnapshotContributor(
            dimension_name=dimension,
            entity_name=entity,
            value=float(item.metric_value),
        )
        dimension_name = dimension
        if role == CONTRIBUTOR_HIGHEST:
            highest = contributor
        else:
            lowest = contributor

    if dimension_name is None or highest is None or lowest is None:
        return None
    return dimension_name, highest, lowest


def _single_bucket_label(df: pd.DataFrame, date_column: str) -> str:
    parsed_dates = _parse_date_column(df[date_column]).dropna().sort_values()
    if parsed_dates.empty:
        return "Single period"
    return _format_date(parsed_dates.iloc[0])


def build_snapshot_context(
    working_df: pd.DataFrame,
    date_column: str,
    *,
    temporal_period_label: str | None = None,
) -> SnapshotContext | None:
    """Return snapshot metadata when the scoped dataset has one temporal bucket."""
    bucket_count = count_distinct_temporal_buckets(working_df, date_column)
    if bucket_count != 1:
        return None

    period_label = temporal_period_label or _single_bucket_label(working_df, date_column)
    return SnapshotContext(
        activated=True,
        reason=SNAPSHOT_REASON,
        period_label=period_label,
        bucket_count=bucket_count,
    )


class SnapshotAnalysisTool:
    """Analyze a single temporal period against a full-dataset baseline."""

    def analyze(
        self,
        scoped_df: pd.DataFrame,
        baseline_df: pd.DataFrame,
        date_column: str,
        metric_column: str,
        *,
        aggregation: AggregationType | None = None,
        period_label: str | None = None,
        dimension_column: str | None = None,
    ) -> ToolResult:
        if scoped_df is None or not isinstance(scoped_df, pd.DataFrame):
            raise ValueError("scoped_df must be a pandas DataFrame")
        if baseline_df is None or not isinstance(baseline_df, pd.DataFrame):
            raise ValueError("baseline_df must be a pandas DataFrame")
        if scoped_df.empty:
            raise ValueError("scoped_df must not be empty")
        if baseline_df.empty:
            raise ValueError("baseline_df must not be empty")
        if date_column not in scoped_df.columns:
            raise ValueError(f"date_column '{date_column}' not found in scoped_df")
        if date_column not in baseline_df.columns:
            raise ValueError(f"date_column '{date_column}' not found in baseline_df")
        if metric_column not in scoped_df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in scoped_df")
        if metric_column not in baseline_df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in baseline_df")

        aggregation = aggregation or infer_aggregation_type(metric_column)
        label = period_label or _single_bucket_label(scoped_df, date_column)

        scoped_periods = _aggregate_by_period(
            scoped_df,
            date_column,
            metric_column,
            aggregation,
        )
        if scoped_periods.empty:
            return ToolResult(
                tool_name="snapshot_analysis",
                success=False,
                summary=(
                    f"No usable data remained for snapshot analysis of "
                    f"'{metric_column}' in '{date_column}'."
                ),
                evidence_items=[],
                warnings=[
                    "No usable data remaining after dropping rows with invalid dates "
                    f"or missing values in '{date_column}' or '{metric_column}'."
                ],
            )

        baseline_periods = _aggregate_by_period(
            baseline_df,
            date_column,
            metric_column,
            aggregation,
        )
        if baseline_periods.empty:
            return ToolResult(
                tool_name="snapshot_analysis",
                success=False,
                summary=(
                    f"No usable baseline data remained for snapshot analysis of "
                    f"'{metric_column}'."
                ),
                evidence_items=[],
                warnings=[
                    "Baseline dataset did not contain usable dated metric values."
                ],
            )

        period_value = float(scoped_periods.iloc[0])
        baseline_value = float(baseline_periods.mean())
        delta = period_value - baseline_value
        scoped_row_count = len(
            scoped_df[[date_column, metric_column]]
            .dropna(subset=[date_column, metric_column])
        )
        baseline_row_count = len(
            baseline_df[[date_column, metric_column]]
            .dropna(subset=[date_column, metric_column])
        )

        period_date = scoped_periods.index[0]
        delta_direction = "above" if delta > 0 else "below" if delta < 0 else "equal to"

        summary = (
            f"For {label}, '{metric_column}' was {period_value:g} "
            f"({aggregation} over the scoped period), "
            f"{delta_direction} the full-dataset baseline of {baseline_value:g} "
            f"(delta {delta:+g})."
        )

        evidence_items = [
            EvidenceItem(
                description=f"Snapshot value for {label}.",
                metric_name=metric_column,
                metric_value=period_value,
                supporting_context=build_supporting_context(
                    {
                        date_column: _format_date(period_date),
                        "aggregation": aggregation,
                        "analysis_mode": "snapshot",
                        "period_label": label,
                        "scoped_row_count": scoped_row_count,
                        "baseline_scope": BASELINE_SCOPE,
                    },
                    metric_column,
                    period_value,
                ),
            ),
            EvidenceItem(
                description="Full-dataset baseline comparison.",
                metric_name=metric_column,
                metric_value=baseline_value,
                supporting_context=build_supporting_context(
                    {
                        "aggregation": aggregation,
                        "analysis_mode": "snapshot",
                        "baseline_scope": BASELINE_SCOPE,
                        "baseline_row_count": baseline_row_count,
                        "baseline_period_count": int(baseline_periods.shape[0]),
                        "delta_vs_baseline": delta,
                    },
                    metric_column,
                    baseline_value,
                ),
            ),
        ]

        if dimension_column:
            contributors = resolve_snapshot_contributors(
                scoped_df,
                dimension_column,
                metric_column,
                aggregation,
            )
            if contributors is not None:
                highest, lowest = contributors
                evidence_items.extend(
                    [
                        EvidenceItem(
                            description=f"Highest contributor for {label}.",
                            metric_name=metric_column,
                            metric_value=highest.value,
                            supporting_context=build_supporting_context(
                                {
                                    "aggregation": aggregation,
                                    "analysis_mode": "snapshot",
                                    "is_snapshot_contributor": True,
                                    "contributor_role": CONTRIBUTOR_HIGHEST,
                                    "dimension_name": highest.dimension_name,
                                    "entity_name": highest.entity_name,
                                },
                                metric_column,
                                highest.value,
                            ),
                        ),
                        EvidenceItem(
                            description=f"Lowest contributor for {label}.",
                            metric_name=metric_column,
                            metric_value=lowest.value,
                            supporting_context=build_supporting_context(
                                {
                                    "aggregation": aggregation,
                                    "analysis_mode": "snapshot",
                                    "is_snapshot_contributor": True,
                                    "contributor_role": CONTRIBUTOR_LOWEST,
                                    "dimension_name": lowest.dimension_name,
                                    "entity_name": lowest.entity_name,
                                },
                                metric_column,
                                lowest.value,
                            ),
                        ),
                    ]
                )
                summary = (
                    f"{summary} Highest contributor: {highest.entity_name} "
                    f"({highest.value:g}). Lowest contributor: {lowest.entity_name} "
                    f"({lowest.value:g})."
                )

        return ToolResult(
            tool_name="snapshot_analysis",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=[],
        )
