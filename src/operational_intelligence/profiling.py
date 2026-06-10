import pandas as pd
from src.operational_intelligence.models import DatasetProfile


class DatasetProfiler:
    """
    Profiles a pandas DataFrame and produces a domain-agnostic DatasetProfile.
    """

    def profile_dataframe(self, dataset_name: str, df: pd.DataFrame) -> DatasetProfile:
        """
        Analyze a pandas DataFrame and return a DatasetProfile describing its structure and basic stats.
        """
        dataset_name = str(dataset_name).strip()
        if not dataset_name:
            raise ValueError("dataset_name must not be empty")
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if df.empty or df.shape[1] == 0:
            raise ValueError("Input DataFrame is empty")

        column_names: list[str] = [str(col) for col in df.columns]
        row_count = int(df.shape[0])
        column_count = int(df.shape[1])
        missing_value_count = int(df.isnull().sum().sum())

        date_columns: list[str] = self._detect_date_columns(df)
        categorical_columns: list[str] = [
            col for col in df.select_dtypes(include=["object", "category", "string"]).columns
            if col not in date_columns
        ]
        numeric_columns: list[str] = self._detect_numeric_columns(df)
        potential_metrics: list[str] = [
            col for col in numeric_columns if not self._is_id_like(col)
        ]
        potential_dimensions: list[str] = list(categorical_columns)

        suitable_tools: list[str] = []
        if date_columns and numeric_columns:
            suitable_tools.append("trend_analysis")
        if categorical_columns and numeric_columns:
            suitable_tools.append("variance_analysis")
        if numeric_columns:
            suitable_tools.append("anomaly_detection")
        if numeric_columns or categorical_columns:
            suitable_tools.append("risk_assessment")

        return DatasetProfile(
            dataset_name=dataset_name,
            row_count=row_count,
            column_count=column_count,
            column_names=column_names,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            date_columns=date_columns,
            missing_value_count=missing_value_count,
            potential_metrics=potential_metrics,
            potential_dimensions=potential_dimensions,
            suitable_tools=suitable_tools,
        )

    def _detect_date_columns(self, df: pd.DataFrame) -> list[str]:
        """
        Identify columns that are dates/datetimes, including object columns that can be reasonably converted.
        Avoids obvious ID/code columns.
        """
        date_columns: list[str] = []

        for col in df.columns:
            series = df[col]

            if pd.api.types.is_datetime64_any_dtype(series):
                date_columns.append(str(col))
                continue

            if self._is_id_like(str(col)):
                continue

            if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                if self._is_series_date_like(series):
                    date_columns.append(str(col))

        return date_columns

    def _is_series_date_like(
        self,
        series: pd.Series,
        sample_size: int = 50,
        success_threshold: float = 0.7,
    ) -> bool:
        """
        Return True when most non-empty sampled values can be parsed as dates.
        """
        try:
            sample = series.dropna().astype(str).head(sample_size)
            if sample.empty:
                return False

            parsed = pd.to_datetime(sample, errors="coerce")
            success_ratio = parsed.notna().mean()

            return bool(success_ratio >= success_threshold)
        except Exception:
            return False

    def _detect_numeric_columns(self, df: pd.DataFrame) -> list[str]:
        """
        Return all numeric columns in the DataFrame.
        """
        return [str(col) for col in df.select_dtypes(include=["number"]).columns]

    def _is_id_like(self, colname: str) -> bool:
        """
        Returns True if column name appears to refer to an ID, code, or number.
        """
        lowered = colname.lower()
        return (
            "id" in lowered
            or lowered.endswith("_id")
            or "code" in lowered
            or "number" in lowered or "no" in lowered
        )
