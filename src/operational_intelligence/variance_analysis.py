import pandas as pd
from src.operational_intelligence.models import ToolResult, EvidenceItem

class VarianceAnalysisTool:
    """
    Compares metric values across categories and summarizes key differences.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        dimension_column: str,
        metric_column: str
    ) -> ToolResult:
        """
        Analyze variance of a metric across dimension categories.

        Args:
            df: DataFrame with the data.
            dimension_column: Column to group by (categorical).
            metric_column: Numeric column to aggregate.

        Returns:
            ToolResult: Result containing evidence and summary.
        """
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        if dimension_column not in df.columns:
            raise ValueError(f"dimension_column '{dimension_column}' not found in DataFrame")
        if metric_column not in df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in DataFrame")

        # Work on a copy for data safety
        data = df[[dimension_column, metric_column]].copy()

        # Drop rows with missing dimension or metric values
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
                    f"No usable data remaining after dropping rows with missing '{dimension_column}' or '{metric_column}'."
                ]
            )

        # Aggregate metric by category (dimension)
        grouped = (
            data.groupby(dimension_column, dropna=False)[metric_column]
            .sum()
            .sort_values(ascending=False)
        )

        evidence_items = []
        for category, metric_value in grouped.items():
            evidence_items.append(
                EvidenceItem(
                    description=(
                        f"For category '{category}', {metric_column} sum = {float(metric_value)}"
                    ),
                    dataset_name=None,
                    metric_name=metric_column,
                    metric_value=float(metric_value) if pd.notnull(metric_value) else None,
                    supporting_context={dimension_column: category}
                )
            )

        num_categories = len(grouped)
        if num_categories == 0:
            summary = (
                f"No valid categories found for dimension '{dimension_column}'."
            )
        else:
            highest_value = grouped.max()
            lowest_value = grouped.min()

            highest_categories = grouped[grouped == highest_value].index.tolist()
            lowest_categories = grouped[grouped == lowest_value].index.tolist()

            highest_label = ", ".join(str(category) for category in highest_categories)
            lowest_label = ", ".join(str(category) for category in lowest_categories)

            summary = (
                f"Analyzed {num_categories} categories in '{dimension_column}'. "
                f"The highest total '{metric_column}' was for {highest_label} ({highest_value}). "
                f"The lowest total '{metric_column}' was for {lowest_label} ({lowest_value})."
            )

        return ToolResult(
            tool_name="variance_analysis",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=[]
        )