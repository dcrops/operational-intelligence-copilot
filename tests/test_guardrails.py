"""
Guardrail tests for unsupported or out-of-scope question types.

Causal attribution is not a supported capability. Causation language triggers a
disclaimer in direct answers while descriptive analytics continue to run.
"""

from __future__ import annotations

import pytest

from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest
from src.operational_intelligence.question_semantics import (
    CAUSATION_DISCLAIMER,
    CAUSATION_FINDINGS_INTRO,
    causation_requested,
)
from ui.analysis_service import run_analysis
from tests.support.assertions import assert_clarification, assert_no_causation_claims
from tests.support.factories import education_bundle, manufacturing_bundle, workforce_bundle


@pytest.mark.unit
@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What caused attendance to drop?", True),
        ("Why did downtime increase?", True),
        ("What led to the increase in overtime?", True),
        ("What changed over time?", False),
        ("What looks unusual?", False),
    ],
)
def test_causation_requested_detection(question: str, expected: bool):
    assert causation_requested(question) is expected


@pytest.mark.integration
class TestCausalQuestionGuardrails:
    def test_causal_question_still_requests_clarification_when_ambiguous(self):
        df, profile = education_bundle()
        result = run_analysis(
            "What caused attendance to drop?",
            df,
            profile,
        )

        assert result.findings == []
        assert result.direct_answer == ""
        assert_clarification(result, "dimension")

    def test_causal_question_routing_is_unchanged_after_clarification(self):
        df, profile = education_bundle()
        result = run_analysis(
            "What caused attendance to drop?",
            df,
            profile,
            selected_metrics=["attendance_rate"],
            selected_dimensions=["school"],
        )

        assert "trend_analysis" in result.routes
        assert result.findings
        assert result.direct_answer.startswith(CAUSATION_DISCLAIMER)
        assert CAUSATION_FINDINGS_INTRO in result.direct_answer
        assert_no_causation_claims(result.direct_answer)

    @pytest.mark.parametrize(
        ("bundle_fn", "question", "selected_metrics"),
        [
            (manufacturing_bundle, "Why did downtime increase?", ["downtime_minutes"]),
            (workforce_bundle, "What led to the increase in overtime?", ["overtime_hours"]),
        ],
    )
    def test_causal_questions_across_domains_include_disclaimer_with_findings(
        self,
        bundle_fn,
        question,
        selected_metrics,
    ):
        df, profile = bundle_fn()
        routes = IntentRouter().route(
            AnalysisRequest(question=question, dataset_names=[profile.dataset_name]),
            [profile],
        )
        assert "trend_analysis" in routes

        result = run_analysis(
            question,
            df,
            profile,
            selected_metrics=selected_metrics,
        )

        assert result.clarification is None
        assert result.direct_answer.startswith(CAUSATION_DISCLAIMER)
        assert CAUSATION_FINDINGS_INTRO in result.direct_answer
        assert result.findings
        assert_no_causation_claims(result.direct_answer)

    def test_non_causal_questions_do_not_include_disclaimer(self):
        df, profile = education_bundle()
        result = run_analysis(
            "How has attendance changed over time?",
            df,
            profile,
        )

        assert result.clarification is None
        assert CAUSATION_DISCLAIMER not in result.direct_answer
        assert result.findings

    def test_anomaly_question_does_not_include_causation_disclaimer(self):
        df, profile = workforce_bundle()
        result = run_analysis(
            "What looks unusual?",
            df,
            profile,
        )

        assert result.clarification is None
        assert CAUSATION_DISCLAIMER not in result.direct_answer
        assert result.findings
