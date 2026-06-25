"""Architecture boundary tests for Milestone 11a — AI Integration Boundary."""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    GENERATOR_TYPE,
    LIMITATIONS,
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import is_narrative_enabled
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    NarrativeRequest,
)
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.assertions import assert_run_analysis_complete
from tests.support.factories import manufacturing_bundle
from ui.analysis_service import run_analysis
from ui.narrative_service import build_deterministic_analysis_snapshot, maybe_generate_narrative


def _sample_snapshot() -> DeterministicAnalysisSnapshot:
    return DeterministicAnalysisSnapshot(
        question="Which line has the highest defects?",
        direct_answer="Line B has the highest defects.",
        executive_summary="Defect concentration is elevated on Line B.",
        analytical_findings=("Defect variance: Line B exceeds Line A.",),
        operational_assessment="critical: Defect load requires immediate review.",
        executive_conclusions=("Address Line B defect rate.",),
        priority_actions=("Inspect Line B tooling.",),
        transparency_summary=("Temporal filter: none applied.",),
        reasoning_trace=("Theme 1: Defect concentration",),
        source_sections=(
            "Direct Answer",
            "Executive Summary",
            "Analytical Findings",
            "Operational Assessment",
            "Executive Conclusions",
            "Priority Actions",
            "System Transparency",
        ),
    )


class TestNarrativeFeatureFlag:
    def test_narrative_disabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        assert is_narrative_enabled() is False

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )
        assert_run_analysis_complete(result)
        assert result.narrative is None


class TestNarrativeRequestBuilder:
    def test_builder_creates_request_from_deterministic_snapshot(self) -> None:
        snapshot = _sample_snapshot()
        request = NarrativeRequestBuilder().build(snapshot)

        assert isinstance(request, NarrativeRequest)
        assert request.question == snapshot.question
        assert request.direct_answer == snapshot.direct_answer
        assert request.executive_summary == snapshot.executive_summary
        assert request.analytical_findings == snapshot.analytical_findings
        assert request.operational_assessment == snapshot.operational_assessment
        assert request.executive_conclusions == snapshot.executive_conclusions
        assert request.priority_actions == snapshot.priority_actions
        assert request.transparency_summary == snapshot.transparency_summary
        assert request.reasoning_trace == snapshot.reasoning_trace
        assert request.source_sections == snapshot.source_sections


class TestNarrativeModels:
    def test_narrative_request_is_immutable(self) -> None:
        request = NarrativeRequestBuilder().build(_sample_snapshot())
        with pytest.raises(FrozenInstanceError):
            request.question = "changed"  # type: ignore[misc]


def _sample_artifact():
    request = NarrativeRequestBuilder().build(_sample_snapshot())
    return PromptArtifactBuilder().build(request)


class TestDeterministicNarrativeGenerator:
    def test_returns_same_response_for_same_request(self) -> None:
        artifact = _sample_artifact()
        generator = DeterministicNarrativeGenerator()

        first = generator.generate(artifact)
        second = generator.generate(artifact)

        assert first == second

    def test_identifies_as_deterministic_not_llm(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        assert response.generator_type == GENERATOR_TYPE
        assert response.generator_type == "deterministic"
        assert "AI-generated executive communication is not enabled" not in response.limitations
        assert response.limitations == LIMITATIONS
        assert "finding-" not in "\n".join(
            section.content for section in response.sections
        ).lower()


class TestNarrativeIntegration:
    def test_enabled_narrative_preserves_deterministic_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OIC_NARRATIVE_ENABLED", raising=False)
        df, profile = manufacturing_bundle()
        question = "Which production line has the highest defects?"

        baseline = run_analysis(question, df, profile)
        assert baseline.narrative is None

        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")
        enabled = run_analysis(question, df, profile)

        assert enabled.narrative is not None
        assert enabled.narrative.generator_type == "deterministic"
        assert enabled.request == baseline.request
        assert enabled.routes == baseline.routes
        assert enabled.findings == baseline.findings
        assert enabled.report == baseline.report
        assert enabled.direct_answer == baseline.direct_answer
        assert enabled.deterministic_answer == baseline.deterministic_answer
        assert enabled.metrics_analysed == baseline.metrics_analysed
        assert enabled.temporal_filter == baseline.temporal_filter
        assert enabled.snapshot_context == baseline.snapshot_context

    def test_narrative_path_does_not_use_llm_client_or_external_services(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "1")

        def _fail_legacy_llm(*args, **kwargs):
            raise AssertionError("LLMAnswerGenerator must not be called by narrative path")

        monkeypatch.setattr(
            "src.operational_intelligence.llm_answer_generator.LLMAnswerGenerator.generate",
            _fail_legacy_llm,
        )

        generator_calls: list = []
        original_generate = DeterministicNarrativeGenerator.generate

        def tracked_generate(self, artifact):
            generator_calls.append(artifact)
            return original_generate(self, artifact)

        monkeypatch.setattr(DeterministicNarrativeGenerator, "generate", tracked_generate)

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )

        assert result.narrative is not None
        assert result.narrative.generator_type == "deterministic"
        assert len(generator_calls) == 1

    def test_narrative_path_does_not_mutate_analysis_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "yes")

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )
        assert result.report is not None

        findings_before = copy.deepcopy(result.findings)
        report_before = copy.deepcopy(result.report)
        routes_before = copy.copy(result.routes)
        direct_answer_before = result.direct_answer
        clarification_before = result.clarification

        snapshot = build_deterministic_analysis_snapshot(result)
        narrative = maybe_generate_narrative(result)

        assert narrative is not None
        assert result.findings == findings_before
        assert result.report == report_before
        assert result.routes == routes_before
        assert result.direct_answer == direct_answer_before
        assert result.clarification == clarification_before
        assert snapshot.question == result.request.question
        assert snapshot.direct_answer == direct_answer_before
