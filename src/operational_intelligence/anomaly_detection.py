import pandas as pd
from src.operational_intelligence.models import ToolResult, EvidenceItem

class AnomalyDetectionTool:
    """
    Detects unusually high or low values in a DataFrame column using z-score method.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        metric_column: str,
        threshold: float = 2.0
    ) -> ToolResult:
        """
        Detect anomalies based on z-score in the specified metric column.

        Args:
            df: DataFrame with data.
            metric_column: Name of the numeric column to analyze.
            threshold: Z-score threshold for anomaly detection (must be > 0).

        Returns:
            ToolResult: Evidence-based anomaly detection result.
        """
        # Validate inputs
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        if metric_column not in df.columns:
            raise ValueError(f"metric_column '{metric_column}' not found in DataFrame")
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            raise ValueError("threshold must be a positive number")

        # Copy data to avoid mutating the original DataFrame
        data = df[[metric_column]].copy()
        # Drop rows with missing metric values
        data = data.dropna(subset=[metric_column])

        if data.empty:
            return ToolResult(
                tool_name="anomaly_detection",
                success=False,
                summary=(
                    f"No usable data remained after dropping rows with missing values in '{metric_column}'."
                ),
                evidence_items=[],
                warnings=[
                    f"No usable data remaining after dropping rows with missing values in '{metric_column}'."
                ]
            )

        metric_values = data[metric_column].astype(float)
        mean = metric_values.mean()
        std = metric_values.std(ddof=0)

        if std == 0:
            return ToolResult(
                tool_name="anomaly_detection",
                success=True,
                summary=(
                    f"No anomalies can be detected in '{metric_column}' because all values are identical."
                ),
                evidence_items=[],
                warnings=[]
            )

        # Calculate z-scores
        z_scores = (metric_values - mean) / std
        abs_z = z_scores.abs()

        # Find anomalies
        anomalies = data[abs_z >= threshold]
        evidence_items = []
        for idx in anomalies.index:
            value = data.at[idx, metric_column]
            z_score = z_scores.at[idx]
            anomaly_direction = "HIGH" if z_score > 0 else "LOW"
            evidence_items.append(
                EvidenceItem(
                    description=(
                        f"Anomalous value detected in row {idx}: {metric_column} = {value} "
                        f"(z_score = {z_score:.2f}, direction = {anomaly_direction})"
                    ),
                    dataset_name=None,
                    metric_name=metric_column,
                    metric_value=value,
                    supporting_context={
                        "row_index": idx,
                        "mean": mean,
                        "standard_deviation": std,
                        "z_score": float(z_score),
                        "anomaly_direction": anomaly_direction,
                    }
                )
            )

        summary = (
            f"Analyzed column '{metric_column}' for anomalies using z-score threshold {threshold}. "
            f"Detected {len(evidence_items)} anomal{'y' if len(evidence_items) == 1 else 'ies'}."
        )

        return ToolResult(
            tool_name="anomaly_detection",
            success=True,
            summary=summary,
            evidence_items=evidence_items,
            warnings=[]
        )