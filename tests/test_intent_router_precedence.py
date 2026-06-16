import pytest

from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest
from tests.support.factories import education_bundle


@pytest.mark.unit
def test_comparative_question_routes_to_variance_only():
    _, profile = education_bundle()
    request = AnalysisRequest(
        question="Which class is performing best?",
        dataset_names=[profile.dataset_name],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis"]


@pytest.mark.unit
def test_anomaly_question_routes_to_anomaly_only():
    _, profile = education_bundle()
    request = AnalysisRequest(
        question="What looks unusual?",
        dataset_names=[profile.dataset_name],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["anomaly_detection"]


@pytest.mark.unit
def test_trend_question_routes_to_trend_analysis_only():
    _, profile = education_bundle()
    request = AnalysisRequest(
        question="How has attendance changed over time?",
        dataset_names=[profile.dataset_name],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["trend_analysis"]


@pytest.mark.unit
def test_mixed_intent_routes_both_tools_for_clarification():
    _, profile = education_bundle()
    request = AnalysisRequest(
        question="What looks unusual and which department has the highest hours?",
        dataset_names=[profile.dataset_name],
    )
    routes = IntentRouter().route(request, [profile])
    assert routes == ["variance_analysis", "anomaly_detection"]
