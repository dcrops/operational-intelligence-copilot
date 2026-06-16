"""
Guardrail tests for unsupported or out-of-scope question types.

Causal attribution is not a supported capability today. These tests document
current behaviour and prevent silent regression toward unsupported claims.
"""

from __future__ import annotations

import pytest

from ui.analysis_service import run_analysis
from tests.support.assertions import assert_clarification, assert_no_causation_claims
from tests.support.factories import education_bundle


@pytest.mark.integration
class TestCausalQuestionGuardrails:
    def test_causal_question_requests_clarification_instead_of_silent_answer(self):
        df, profile = education_bundle()
        result = run_analysis(
            "What caused attendance to drop?",
            df,
            profile,
        )

        assert result.findings == []
        assert result.direct_answer == ""
        assert_clarification(result, "dimension")

    def test_causal_question_does_not_claim_causation_after_clarification(self):
        df, profile = education_bundle()
        result = run_analysis(
            "What caused attendance to drop?",
            df,
            profile,
            selected_metrics=["attendance_rate"],
            selected_dimensions=["school"],
        )

        combined_output = f"{result.direct_answer}\n{result.deterministic_answer}"
        assert_no_causation_claims(combined_output)
        assert result.findings
        assert all(
            "Trend" in finding.title or "Variance" in finding.title
            for finding in result.findings
        )

    @pytest.mark.xfail(
        reason=(
            "Future capability: explicit unsupported-question handling for causal "
            "questions rather than running descriptive tools after clarification."
        ),
        strict=False,
    )
    def test_future_causal_questions_should_be_rejected_explicitly(self):
        """Placeholder for explicit unsupported-question messaging when implemented."""
        df, profile = education_bundle()
        result = run_analysis(
            "What caused attendance to drop?",
            df,
            profile,
        )
        assert result.clarification is None
        assert "cannot determine causation" in result.direct_answer.lower()
