"""Tests for deterministic narrative presentation quality."""

from __future__ import annotations

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    GENERATOR_TYPE,
    LIMITATIONS,
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_models import DeterministicAnalysisSnapshot
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder

_FORBIDDEN_NARRATIVE_TERMS = (
    "deterministic narrative assembly",
    "not llm-generated",
    "objective:",
    "question:",
    "direct answer:",
    "executive summary:",
    "operational assessment:",
    "executive conclusions:",
    "evidence references",
    "finding-",
    "action-",
    "transparency-",
    "conclusion-",
    "direct-answer",
    "executive-summary",
)


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


def _sample_artifact():
    request = NarrativeRequestBuilder().build(_sample_snapshot())
    return PromptArtifactBuilder().build(request)


class TestDeterministicNarrativePresentation:
    def test_produces_executive_style_prose(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        assert "Defect concentration is elevated on Line B." in response.executive_narrative
        assert "Line B exceeds Line A." in response.executive_narrative
        assert "Defect load requires immediate review." in response.executive_narrative
        assert "Inspect Line B tooling." in response.executive_narrative

    def test_excludes_implementation_wording(self) -> None:
        narrative = DeterministicNarrativeGenerator().generate(
            _sample_artifact()
        ).executive_narrative.lower()

        for term in _FORBIDDEN_NARRATIVE_TERMS:
            assert term not in narrative, f"Found forbidden term {term!r} in narrative"

    def test_limitations_remain_honest(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        assert response.limitations == LIMITATIONS
        assert "deterministic narrative generator" in response.limitations.lower()
        assert "AI-generated executive communication is not enabled" in response.limitations

    def test_key_message_uses_operational_rationale_when_available(self) -> None:
        response = DeterministicNarrativeGenerator().generate(_sample_artifact())

        assert response.key_message == "Defect load requires immediate review."

    def test_remains_deterministic(self) -> None:
        generator = DeterministicNarrativeGenerator()
        artifact = _sample_artifact()

        assert generator.generate(artifact) == generator.generate(artifact)
        assert generator.generate(artifact).generator_type == GENERATOR_TYPE
