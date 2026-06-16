import pandas as pd

from src.operational_intelligence.models import EvidenceItem, ToolResult
from src.operational_intelligence.question_semantics import (
    DEFAULT_AGGREGATION,
    AggregationType,
    ComparisonDirection,
    aggregation_label,
    infer_aggregation_type,
)


class VarianceAnalysisTool:
    """
    Compares metric values across categories and summarizes key differences.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        dimension_column: str,
        metric_column: str,
        *,
        aggregation: AggregationType | None = None,
        comparison_direction: ComparisonDirection | None = None,
    ) -> ToolResult:
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        if dimension_column not in df.columns:
            raise ValueError(f"dimension_column '{dimension_column}' not found in DataFrame")
        if metric_column not in df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in DataFrame")

        aggregation = aggregation or infer_aggregation_type(metric_column)
        direction: ComparisonDirection = comparison_direction or "top"
        agg_label = aggregation_label(aggregation)

        data = df[[dimension_column, metric_column]].copy()
        data = data.dropna(subset=[dimension_column, metric_column])

        if data.empty:
            return ToolResult(
                tool_name="variance_analysis",
                success=False,
                summary=(
                    f"No usable data remained after dropping rows with missing values in "
                    f"'{dimension_column}' or '{metric_column}'."
                ),
                evidence_items=[],
                warnings=[
                    f"No usable data remaining after dropping rows with missing "
                    f"'{dimension_column}' or '{metric_column}'."
                ],
            )

        grouped = data.groupby(dimension_column, dropna=False)[metric_column]
        if aggregation == "mean":
            aggregated = grouped.mean()
        else:
            aggregated = grouped.sum()
        aggregated = aggregated.sort_values(ascending=False)

        top_value = float(aggregated.max())
        bottom_value = float(aggregated.min())
        top_categories = aggregated[aggregated == top_value].index.tolist()
        bottom_categories = aggregated[aggregated == bottom_value].index.tolist()

        target_categories: set[object] = set()
        if direction == "top":
            target_categories.update(top_categories)
        elif direction == "bottom":
            target_categories.update(bottom_categories)
        else:
            target_categories.update(top_categories)
            target_categories.update(bottom_categories)

        evidence_items: list[EvidenceItem] = []
        for category, metric_value in aggregated.items():
            context = {
                dimension_column: category,
                "aggregation": aggregation,
                "comparison_direction": direction,
                "is_comparison_target": category in target_categories,
            }
            if direction == "dual" and category in target_categories:
                context["comparison_extreme"] = (
                    "top" if category in top_categories else "bottom"
                )

            evidence_items.append(
                EvidenceItem(
                    description=(
                        f"For category '{category}', {metric_column} {agg_label} = "
                        f"{float(metric_value)}"
                    ),
                    dataset_name=None,
                    metric_name=metric_column,
                    metric_value=float(metric_value) if pd.notnull(metric_value) else None,
                    supporting_context=context,
                )
            )

        num_categories = len(aggregated)
        if num_categories == 0:
            summary = f"No valid categories found for dimension '{dimension_column}'."
        else:
            top_label = ", ".join(str(category) for category in top_categories)
            bottom_label = ", ".join(str(category) for category in bottom_categories)

            if direction == "bottom":
                summary = (
                    f"Analyzed {num_categories} categories in '{dimension_column}'. "
                    f"The lowest {agg_label} '{metric_column}' was for {bottom_label} "
                    f"({bottom_value})."
                )
            elif direction == "dual":
                summary = (
                    f"Analyzed {num_categories} categories in '{dimension_column}'. "
                    f"The highest {agg_label} '{metric_column}' was for {top_label} "
                    f"({top_value}). The lowest {agg_label} '{metric_column}' was for "
                    f"{bottom_label} ({bottom_value})."
                )
            else:
                summary = (
                    f"Analyzed {num_categories} categories in '{dimension_column}'. "
                    f"The highest {agg_label} '{metric_column}' was for {top_label} "
                    f"({top_value}). The lowest {agg_label} '{metric_column}' was for "
                    f"{bottom_label} ({bottom_value})."
                )

        return ToolResult(
            tool_name="variance_analysis",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=[],
        )
