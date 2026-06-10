import pandas as pd
import pytest
from src.operational_intelligence.profiling import DatasetProfiler

def test_basic_profiling_mixed_dataframe():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "category": ["A", "B", "A"],
        "value": [10.0, 20.1, 25],
        "date": pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]),
        "note": ["foo", "bar", "baz"],
        "missing": [None, None, None],
    })
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("TestDataset", df)
    # Field assertions
    assert profile.dataset_name == "TestDataset"
    assert profile.row_count == 3
    assert profile.column_count == 6
    assert set(profile.column_names) == set(df.columns)
    assert set(profile.numeric_columns) == {"id", "value"}
    assert set(profile.categorical_columns) == {"category", "note", "missing"}
    assert set(profile.date_columns) == {"date"}
    assert profile.missing_value_count == 3
    # id should not be in potential_metrics
    assert "id" not in profile.potential_metrics
    assert "value" in profile.potential_metrics
    # category column should be in potential_dimensions
    assert "category" in profile.potential_dimensions
    # suitable_tools checks
    assert "trend_analysis" in profile.suitable_tools
    assert "variance_analysis" in profile.suitable_tools
    assert "anomaly_detection" in profile.suitable_tools
    assert "risk_assessment" in profile.suitable_tools

def test_dataset_name_whitespace_trimming():
    df = pd.DataFrame({"x": [1,2]})
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("  mydataset  ", df)
    assert profile.dataset_name == "mydataset"

def test_empty_dataset_name_raises_value_error():
    df = pd.DataFrame({"a": [1, 2]})
    profiler = DatasetProfiler()
    with pytest.raises(ValueError, match="dataset_name must not be empty"):
        profiler.profile_dataframe("   ", df)

def test_non_dataframe_input_raises_value_error():
    profiler = DatasetProfiler()
    with pytest.raises(ValueError, match="df must be a pandas DataFrame"):
        profiler.profile_dataframe("NonDF", [1,2,3])

def test_empty_dataframe_raises_value_error():
    profiler = DatasetProfiler()
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        profiler.profile_dataframe("Empty", empty_df)

def test_id_like_column_handling():
    df = pd.DataFrame({
        "customer_id": [101, 102, 103],
        "accountNo": [2001, 2002, 2003],
        "amount": [5.5, 8.1, 7.0],
        "description": ["foo", "bar", "baz"],
    })
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("Test", df)
    # All numeric columns
    assert set(profile.numeric_columns) == {"customer_id", "accountNo", "amount"}
    # ID-like columns not in potential_metrics
    assert "customer_id" not in profile.potential_metrics
    assert "accountNo" not in profile.potential_metrics
    assert "amount" in profile.potential_metrics

def test_string_date_columns_are_detected():
    df = pd.DataFrame({
        "open_date": ["2022-01-01", "2022-02-01", "2022-01-03"],
        "value": [1, 2, 3]
    })
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("Sample", df)
    assert "open_date" in profile.date_columns

def test_suitable_tools_trend_analysis_triggered_by_date_and_numeric():
    df = pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=4),
        "value": [100, 200, 150, 120]
    })
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("DatesAndNums", df)
    assert "trend_analysis" in profile.suitable_tools

def test_suitable_tools_variance_analysis_triggered_by_categorical_and_numeric():
    df = pd.DataFrame({
        "group": ["X", "Y", "X"],
        "score": [1.5, 2.1, 2.2]
    })
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("CatNum", df)
    assert "variance_analysis" in profile.suitable_tools

def test_suitable_tools_anomaly_detection_numeric_only():
    df = pd.DataFrame({"num1": [1,2,3], "num2": [4,5,6]})
    profiler = DatasetProfiler()
    profile = profiler.profile_dataframe("NumsOnly", df)
    assert "anomaly_detection" in profile.suitable_tools

def test_suitable_tools_risk_assessment_with_numeric_or_categorical():
    df1 = pd.DataFrame({"cat": ["A", "B"]})
    df2 = pd.DataFrame({"num": [1,2]})
    profiler = DatasetProfiler()
    profile_cat = profiler.profile_dataframe("WithCat", df1)
    profile_num = profiler.profile_dataframe("WithNum", df2)
    assert "risk_assessment" in profile_cat.suitable_tools
    assert "risk_assessment" in profile_num.suitable_tools