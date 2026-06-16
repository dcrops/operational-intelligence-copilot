from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.operational_intelligence.models import EvidenceItem, ToolResult
from src.operational_intelligence.question_semantics import (
    AggregationType,
    aggregation_label,
    infer_aggregation_type,
)

DIRECTION_THRESHOLD = 0.02
REVERSAL_THRESHOLD = 2
PATH_EFFICIENCY_THRESHOLD = 3.0
MATERIAL_STEP_RATIO = 0.05
MIN_PERIODS_FOR_RELIABLE_TREND = 3


@dataclass(frozen=True)
class TrendClassification:
    trend_label: str
    pct_change: float | None
    pct_change_percent: float | None
    normalized_slope: float
    reversals: int
    positive_steps: int
    negative_steps: int
    cv: float | None
    range_ratio: float | None
    n_periods: int
    warnings: tuple[str, ...]


def _format_date(value: object) -> str:
    if hasattr(value, "date"):
        return str(value.date())
    return str(value)


def _count_reversals(diffs: list[float]) -> int:
    reversals = 0
    previous_sign = 0

    for diff in diffs:
        if diff == 0:
            continue

        sign = 1 if diff > 0 else -1
        if previous_sign != 0 and sign != previous_sign:
            reversals += 1
        previous_sign = sign

    return reversals


def _compute_trend_metrics(values: list[float]) -> dict[str, float | int | None]:
    n = len(values)
    first_value = values[0]
    last_value = values[-1]
    mean_value = sum(values) / n

    if first_value == 0:
        pct_change = None
        pct_change_percent = None
    else:
        pct_change = (last_value - first_value) / abs(first_value)
        pct_change_percent = pct_change * 100

    if n >= 2 and mean_value != 0:
        x_mean = (n - 1) / 2.0
        numerator = sum(
            (index - x_mean) * (value - mean_value)
            for index, value in enumerate(values)
        )
        denominator = sum((index - x_mean) ** 2 for index in range(n))
        slope = numerator / denominator if denominator else 0.0
        normalized_slope = slope / abs(mean_value)
    else:
        normalized_slope = 0.0

    diffs = [values[index + 1] - values[index] for index in range(n - 1)]
    positive_steps = sum(1 for diff in diffs if diff > 0)
    negative_steps = sum(1 for diff in diffs if diff < 0)
    reversals = _count_reversals(diffs)

    if n > 1 and mean_value != 0:
        variance = sum((value - mean_value) ** 2 for value in values) / n
        std_dev = variance ** 0.5
        cv = std_dev / abs(mean_value)
        range_ratio = (max(values) - min(values)) / abs(mean_value)
    else:
        cv = None
        range_ratio = None

    total_variation = sum(abs(diff) for diff in diffs)
    net_change = abs(last_value - first_value)
    path_efficiency = (
        total_variation / net_change
        if net_change > 0 and diffs
        else None
    )
    mean_abs_step = total_variation / len(diffs) if diffs else 0.0
    mean_abs_step_ratio = (
        mean_abs_step / abs(mean_value)
        if mean_value != 0
        else None
    )

    return {
        "pct_change": pct_change,
        "pct_change_percent": pct_change_percent,
        "normalized_slope": normalized_slope,
        "reversals": reversals,
        "positive_steps": positive_steps,
        "negative_steps": negative_steps,
        "cv": cv,
        "range_ratio": range_ratio,
        "path_efficiency": path_efficiency,
        "mean_abs_step_ratio": mean_abs_step_ratio,
        "n_periods": n,
    }


def _classify_trend(values: list[float]) -> TrendClassification:
    warnings: list[str] = []
    metrics = _compute_trend_metrics(values)
    n_periods = int(metrics["n_periods"])

    if n_periods < MIN_PERIODS_FOR_RELIABLE_TREND:
        warnings.append(
            "Fewer than 3 periods available; trend classification may be less reliable."
        )

    pct_change = metrics["pct_change"]
    normalized_slope = float(metrics["normalized_slope"])
    reversals = int(metrics["reversals"])
    positive_steps = int(metrics["positive_steps"])
    negative_steps = int(metrics["negative_steps"])
    path_efficiency = metrics["path_efficiency"]
    mean_abs_step_ratio = metrics["mean_abs_step_ratio"]

    threshold = DIRECTION_THRESHOLD
    strong_up = (
        pct_change is not None
        and pct_change >= threshold
        and normalized_slope >= threshold
    )
    strong_down = (
        pct_change is not None
        and pct_change <= -threshold
        and normalized_slope <= -threshold
    )

    weak_direction = (
        pct_change is None or abs(float(pct_change)) < threshold
    ) and abs(normalized_slope) < threshold
    reversal_dominated = reversals >= REVERSAL_THRESHOLD
    inconsistent_direction = (
        pct_change is not None
        and normalized_slope != 0
        and (float(pct_change) * normalized_slope) < 0
    )
    balanced_steps = positive_steps >= 2 and negative_steps >= 2
    inefficient_path = (
        path_efficiency is not None
        and path_efficiency > PATH_EFFICIENCY_THRESHOLD
    )
    material_movement = (
        mean_abs_step_ratio is not None
        and mean_abs_step_ratio >= MATERIAL_STEP_RATIO
    )

    volatile = reversal_dominated and (
        inconsistent_direction
        or (balanced_steps and inefficient_path)
        or (weak_direction and balanced_steps and material_movement)
    )

    if volatile:
        trend_label = "volatile"
    elif strong_up:
        trend_label = "increasing"
    elif strong_down:
        trend_label = "decreasing"
    elif weak_direction:
        trend_label = "stable"
    elif pct_change is not None and float(pct_change) > 0:
        trend_label = "increasing"
    elif pct_change is not None and float(pct_change) < 0:
        trend_label = "decreasing"
    elif normalized_slope > 0:
        trend_label = "increasing"
    elif normalized_slope < 0:
        trend_label = "decreasing"
    else:
        trend_label = "stable"

    return TrendClassification(
        trend_label=trend_label,
        pct_change=float(pct_change) if pct_change is not None else None,
        pct_change_percent=(
            float(metrics["pct_change_percent"])
            if metrics["pct_change_percent"] is not None
            else None
        ),
        normalized_slope=normalized_slope,
        reversals=reversals,
        positive_steps=positive_steps,
        negative_steps=negative_steps,
        cv=float(metrics["cv"]) if metrics["cv"] is not None else None,
        range_ratio=(
            float(metrics["range_ratio"])
            if metrics["range_ratio"] is not None
            else None
        ),
        n_periods=n_periods,
        warnings=tuple(warnings),
    )


def _build_trend_summary(
    *,
    metric_column: str,
    first_date: object,
    last_date: object,
    first_value: float,
    last_value: float,
    classification: TrendClassification,
) -> str:
    first_label = _format_date(first_date)
    last_label = _format_date(last_date)
    pct_str = (
        f" ({classification.pct_change_percent:.1f}% change)"
        if classification.pct_change_percent is not None
        else ""
    )
    prefix = (
        f"Between {first_label} and {last_label}, "
        f"the metric '{metric_column}' changed from {first_value:g} to {last_value:g}{pct_str}. "
    )

    if classification.trend_label == "increasing":
        return prefix + "Overall, the trend increased."
    if classification.trend_label == "decreasing":
        return prefix + "Overall, the trend decreased."
    if classification.trend_label == "volatile":
        return (
            f"Between {first_label} and {last_label}, "
            f"the metric '{metric_column}' moved up and down repeatedly "
            f"with no consistent directional movement. "
            "Overall, the trend was volatile, with significant fluctuations across periods."
        )
    return prefix + "Overall, the trend remained stable."


def _build_classification_context(
    classification: TrendClassification,
) -> dict[str, str | int | float | bool | None]:
    return {
        "trend_label": classification.trend_label,
        "n_periods": classification.n_periods,
        "pct_change": classification.pct_change,
        "pct_change_percent": classification.pct_change_percent,
        "normalized_slope": classification.normalized_slope,
        "reversals": classification.reversals,
        "positive_steps": classification.positive_steps,
        "negative_steps": classification.negative_steps,
        "cv": classification.cv,
        "range_ratio": classification.range_ratio,
    }


class TrendAnalysisTool:
    """
    Analyzes the trend of a given metric over time in a pandas DataFrame.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        date_column: str,
        metric_column: str,
        *,
        aggregation: AggregationType | None = None,
    ) -> ToolResult:
        """
        Analyze how a metric changes over time in the DataFrame.

        Args:
            df: DataFrame with data.
            date_column: Name of the column containing dates.
            metric_column: Name of the metric column to analyze.

        Returns:
            ToolResult: Result containing evidence and a summary.
        """
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        if date_column not in df.columns:
            raise ValueError(f"date_column '{date_column}' not found in DataFrame")
        if metric_column not in df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in DataFrame")

        data = df[[date_column, metric_column]].copy()
        data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
        if data[date_column].isnull().all():
            raise ValueError(f"All values in '{date_column}' could not be converted to datetime")
        data = data.dropna(subset=[date_column])
        data = data.dropna(subset=[metric_column])

        if data.empty:
            return ToolResult(
                tool_name="trend_analysis",
                success=False,
                summary=(
                    f"No usable data remained after cleaning "
                    f"'{date_column}' and '{metric_column}'."
                ),
                evidence_items=[],
                warnings=[
                    "No usable data remaining after dropping rows with invalid dates "
                    f"or missing values in '{date_column}' or '{metric_column}'."
                ],
            )

        data = data.sort_values(by=date_column)
        aggregation = aggregation or infer_aggregation_type(metric_column)
        grouped_frame = data.groupby(date_column, dropna=False)[metric_column]
        if aggregation == "mean":
            grouped = grouped_frame.mean()
        else:
            grouped = grouped_frame.sum()
        grouped = grouped.sort_index()

        evidence_items: list[EvidenceItem] = []
        for timestamp, metric_value in grouped.items():
            evidence_items.append(
                EvidenceItem(
                    description=(
                        f"At {_format_date(timestamp)}, "
                        f"{metric_column} = {metric_value}"
                    ),
                    dataset_name=None,
                    metric_name=metric_column,
                    metric_value=float(metric_value) if pd.notnull(metric_value) else None,
                    supporting_context={
                        date_column: str(timestamp),
                        "aggregation": aggregation,
                    },
                )
            )

        warnings: list[str] = []

        if grouped.empty:
            summary = (
                f"No data for metric '{metric_column}' over time in column '{date_column}'."
            )
        else:
            values = [float(value) for value in grouped.tolist()]
            classification = _classify_trend(values)
            warnings.extend(classification.warnings)

            first_date = grouped.index[0]
            last_date = grouped.index[-1]
            first_value = float(grouped.iloc[0])
            last_value = float(grouped.iloc[-1])

            summary = _build_trend_summary(
                metric_column=metric_column,
                first_date=first_date,
                last_date=last_date,
                first_value=first_value,
                last_value=last_value,
                classification=classification,
            )

            evidence_items.append(
                EvidenceItem(
                    description=(
                        "Trend classification summary for the aggregated time series."
                    ),
                    dataset_name=None,
                    metric_name=metric_column,
                    metric_value=last_value,
                    supporting_context=_build_classification_context(classification),
                )
            )

        return ToolResult(
            tool_name="trend_analysis",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=warnings,
        )
