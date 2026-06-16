import pandas as pd
import pytest

from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest
from src.operational_intelligence.profiling import DatasetProfiler


def _education_profile():
    df = pd.read_csv("data/sample/education_demo.csv")
    return DatasetProfiler().profile_dataframe("education_demo", df)


@pytest.mark.unit
def test_comparative_question_routes_to_variance_only():
    profile = _education_profile()
    request = AnalysisRequest(
        question="Which class is performing best?",
        dataset_names=["education_demo"],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis"]


@pytest.mark.unit
def test_anomaly_question_routes_to_anomaly_only():
    profile = _education_profile()
    request = AnalysisRequest(
        question="What looks unusual?",
        dataset_names=["education_demo"],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["anomaly_detection"]


@pytest.mark.unit
def test_trend_question_routes_to_trend_analysis_only():
    profile = _education_profile()
    request = AnalysisRequest(
        question="How has attendance changed over time?",
        dataset_names=["education_demo"],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["trend_analysis"]


@pytest.mark.unit
def test_mixed_intent_routes_both_tools_for_clarification():
    profile = _education_profile()
    request = AnalysisRequest(
        question="What looks unusual and which department has the highest hours?",
        dataset_names=["education_demo"],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis", "anomaly_detection"]
