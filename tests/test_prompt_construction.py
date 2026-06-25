"""Tests for Milestone 11b — Prompt Construction & Narrative Assembly."""

from __future__ import annotations

import dataclasses

import pytest

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    GENERATOR_TYPE,
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_governance import (
    DEFAULT_NARRATIVE_OBJECTIVE,
    OBJECTIVE_EXECUTIVE_SUMMARY,
    PROMPT_ARTIFACT_VERSION,
    PROHIBITED_BEHAVIOURS,
)
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    NarrativeRequest,
    PromptArtifact,
)
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.assertions import assert_run_analysis_complete
from tests.support.factories import manufacturing_bundle
from ui.analysis_service import run_analysis


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


def _sample_request() -> NarrativeRequest:
    return NarrativeRequestBuilder().build(_sample_snapshot())


def _sample_artifact() -> PromptArtifact:
    return PromptArtifactBuilder().build(_sample_request())


class TestPromptArtifactContent:
    def test_contains_required_evidence(self) -> None:
        artifact = _sample_artifact()

        assert artifact.question == "Which line has the highest defects?"
        assert artifact.direct_answer
        assert artifact.executive_summary
        assert artifact.analytical_findings
        assert artifact.evidence_references

        evidence_ids = {ref.evidence_id for ref in artifact.evidence_references}
        assert "direct-answer" in evidence_ids
        assert "executive-summary" in evidence_ids
        assert "finding-1" in evidence_ids
        assert "operational-assessment" in evidence_ids
        assert "conclusion-1" in evidence_ids
        assert "executive-action-1" in evidence_ids
        assert "operational-action-1" in evidence_ids
        assert artifact.executive_context is not None
        assert not any(evidence_id.startswith("transparency-") for evidence_id in evidence_ids)

    def test_excludes_prohibited_fields(self) -> None:
        artifact = _sample_artifact()
        field_names = {field.name for field in dataclasses.fields(PromptArtifact)}

        for prohibited in (
            "model_name",
            "temperature",
            "api_provider",
            "openai_messages",
            "routes",
            "clarification",
            "pipeline_internals",
        ):
            assert prohibited not in field_names

        serialized = repr(artifact).lower()
        assert "openai" not in serialized
        assert "temperature" not in serialized


class TestEvidenceReferenceGeneration:
    def test_evidence_reference_generation_is_deterministic(self) -> None:
        request = _sample_request()
        builder = PromptArtifactBuilder()

        first = builder.build(request).evidence_references
        second = builder.build(request).evidence_references

        assert first == second
        evidence_ids = {reference.evidence_id for reference in first}
        assert "finding-1" in evidence_ids
        assert "key-message" in evidence_ids
        assert "outside normal expectations" in first[-1].content.lower() or any(
            "outside normal expectations" in reference.content.lower() for reference in first
        )

    def test_source_section_traceability_preserved(self) -> None:
        artifact = _sample_artifact()

        assert artifact.source_sections == _sample_request().source_sections
        for reference in artifact.evidence_references:
            assert reference.section in artifact.source_sections


class TestGroundingConstraints:
    def test_grounding_constraints_attached(self) -> None:
        artifact = _sample_artifact()
        constraints = artifact.grounding_constraints

        assert constraints.closed_world is True
        assert constraints.allowed_source_sections == artifact.source_sections
        assert constraints.prohibited_behaviours == PROHIBITED_BEHAVIOURS


class TestPromptArtifactBuilder:
    def test_builder_is_deterministic(self) -> None:
        request = _sample_request()
        builder = PromptArtifactBuilder()

        assert builder.build(request) == builder.build(request)

    def test_artifact_is_reproducible(self) -> None:
        artifacts = [PromptArtifactBuilder().build(_sample_request()) for _ in range(3)]
        assert artifacts[0] == artifacts[1] == artifacts[2]

    def test_default_narrative_objective_is_executive_advisor(self) -> None:
        artifact = _sample_artifact()
        assert artifact.narrative_objective == DEFAULT_NARRATIVE_OBJECTIVE

    def test_supports_executive_summary_objective(self) -> None:
        artifact = PromptArtifactBuilder().build(
            _sample_request(),
            narrative_objective=OBJECTIVE_EXECUTIVE_SUMMARY,
        )
        assert artifact.narrative_objective == OBJECTIVE_EXECUTIVE_SUMMARY

    def test_artifact_version_from_governance(self) -> None:
        assert _sample_artifact().artifact_version == PROMPT_ARTIFACT_VERSION


class TestNarrativePathIntegration:
    def test_narrative_path_remains_deterministic(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OIC_NARRATIVE_ENABLED", "true")

        artifact = _sample_artifact()
        generator = DeterministicNarrativeGenerator()

        assert generator.generate(artifact) == generator.generate(artifact)

    def test_no_openai_calls_occur(
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

        builder_calls: list[NarrativeRequest] = []
        original_build = PromptArtifactBuilder.build

        def tracked_build(self, request, *, narrative_objective=None):
            builder_calls.append(request)
            return original_build(self, request, narrative_objective=narrative_objective)

        monkeypatch.setattr(PromptArtifactBuilder, "build", tracked_build)

        df, profile = manufacturing_bundle()
        result = run_analysis(
            "Which production line has the highest defects?",
            df,
            profile,
        )

        assert_run_analysis_complete(result)
        assert result.narrative is not None
        assert result.narrative.generator_type == GENERATOR_TYPE
        assert len(builder_calls) == 1
