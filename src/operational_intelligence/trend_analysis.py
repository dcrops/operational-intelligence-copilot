import pandas as pd
from src.operational_intelligence.models import ToolResult, EvidenceItem

class TrendAnalysisTool:
    """
    Analyzes the trend of a given metric over time in a pandas DataFrame.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        date_column: str,
        metric_column: str
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
        
        # Work on a copy
        data = df[[date_column, metric_column]].copy()
        
        # Convert date column to datetime
        data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
        if data[date_column].isnull().all():
            raise ValueError(f"All values in '{date_column}' could not be converted to datetime")
        data = data.dropna(subset=[date_column])
        
        # Remove rows with missing metric
        data = data.dropna(subset=[metric_column])

        # If no usable rows remain, return ToolResult with warning
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
                    f"No usable data remaining after dropping rows with invalid dates or missing values in '{date_column}' or '{metric_column}'."
                ]
            )

        # Sort chronologically
        data = data.sort_values(by=date_column)
        
        # Aggregate metric by date
        grouped = data.groupby(date_column, dropna=False)[metric_column].sum()
        grouped = grouped.sort_index()

        # Prepare evidence
        evidence_items = []
        for timestamp, metric_value in grouped.items():
            evidence_items.append(EvidenceItem(
                description=f"At {timestamp.date() if hasattr(timestamp, 'date') else str(timestamp)}, "
                            f"{metric_column} = {metric_value}",
                dataset_name=None,
                metric_name=metric_column,
                metric_value=float(metric_value) if pd.notnull(metric_value) else None,
                supporting_context={date_column: str(timestamp)}
            ))

        if grouped.empty:
            summary = f"No data for metric '{metric_column}' over time in column '{date_column}'."
        else:
            first_date = grouped.index[0]
            last_date = grouped.index[-1]
            first_value = grouped.iloc[0]
            last_value = grouped.iloc[-1]

            # Compute percentage change if first_value is not zero
            if first_value == 0:
                pct_change = None
            else:
                pct_change = ((last_value - first_value) / abs(first_value)) * 100

            # Determine trend
            if pct_change is None:
                trend = "stable" if last_value == first_value else "variable"
            elif pct_change > 2:
                trend = "increased"
            elif pct_change < -2:
                trend = "decreased"
            else:
                trend = "remained stable"
            
            pct_str = (
                f" ({pct_change:.1f}% change)" if pct_change is not None else ""
            )
            summary = (
                f"Between {first_date.date() if hasattr(first_date, 'date') else str(first_date)}"
                f" and {last_date.date() if hasattr(last_date, 'date') else str(last_date)}, "
                f"the metric '{metric_column}' changed from {first_value} to {last_value}{pct_str}. "
                f"Overall, the trend {trend}."
            )
        
        return ToolResult(
            tool_name="trend_analysis",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=[],
        )