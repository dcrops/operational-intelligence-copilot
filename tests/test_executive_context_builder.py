"""Tests for the Executive Context Builder architectural layer."""

from __future__ import annotations

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.executive_context_builder import ExecutiveContextBuilder
from src.operational_intelligence.llm.executive_language import (
    sanitize_executive_prose,
    translate_technical_language,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    ExecutiveContext,
    NarrativeRequest,
)
from src.operational_intelligence.llm.openai_narrative_generator import OpenAINarrativeGenerator
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.openai_provider_config import OpenAIProviderConfig
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from tests.support.fakes import FakeLLMClient

_TECHNICAL_TERMS = (
    "z-score",
    "standard deviation",
    "anomaly threshold",
    "analyzed column",
    "using z-score method",
)

_REPETITIVE_ANALYTICAL_PHRASES = (
    "operational analysis identified",
    "finding(s)",
    "unusual values were identified for",
    "were detected for",
)


def _technical_snapshot() -> DeterministicAnalysisSnapshot:
    return DeterministicAnalysisSnapshot(
        question="Which production line has unusual defect values?",
        direct_answer=(
            "3 unusual high values were detected for defects.\n\n"
            "Examples include:\n"
            "- Line B: defects = 52, compared with an average of 8.2 (z-score 5.08)."
        ),
        executive_summary=(
            "Operational analysis identified 1 finding(s): 1 high priority, 0 medium priority, "
            "and 0 low priority."
        ),
        analytical_findings=(
            "Anomaly detection: Line B defects are far outside expected variation.",
        ),
        operational_assessment="critical: Defect load requires immediate review.",
        executive_conclusions=("Address Line B defect rate.",),
        priority_actions=("Inspect Line B tooling.",),
        transparency_summary=(
            "Temporal filter: none applied.",
            "Dimension: production_line",
        ),
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


def _technical_request() -> NarrativeRequest:
    return NarrativeRequestBuilder().build(_technical_snapshot())


def _combined_context_text(context: ExecutiveContext) -> str:
    return " ".join(
        part
        for part in (
            context.key_message,
            context.assessment_confidence_level,
            context.assessment_confidence_rationale,
            context.executive_assessment_headline,
            context.business_summary,
            context.direct_answer_summary,
            context.why_this_matters,
            context.operational_significance or "",
            context.business_impact or "",
            context.investigation_strategy,
            context.prioritized_explanations,
            *context.key_findings,
            *context.executive_actions,
            *context.operational_investigation_actions,
        )
        if part
    )


class TestExecutiveLanguageTranslation:
    def test_translates_z_score_parenthetical(self) -> None:
        translated = translate_technical_language(
            "Line B: defects = 52, compared with an average of 8.2 (z-score 5.08)."
        )

        assert "z-score" not in translated.lower()
        assert "far outside the normal operating range" in translated.lower()

    def test_sanitize_removes_orphan_number_fragments(self) -> None:
        cleaned = sanitize_executive_prose("Attendance Rate. 5.")

        assert cleaned == "Attendance Rate."


class TestExecutiveContextBuilder:
    def test_builds_executive_context_from_narrative_request(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert isinstance(context, ExecutiveContext)
        assert context.question == _technical_request().question
        assert context.business_summary
        assert context.direct_answer_summary
        assert context.investigation_strategy
        assert context.business_impact
        assert context.decision_guidance

    def test_preserves_deterministic_facts(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        combined = _combined_context_text(context)

        assert "Line B" in combined
        assert "52" in combined or "8.2" in combined

    def test_does_not_hallucinate_evidence(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert "school" not in context.direct_answer_summary.lower()
        assert "payroll" not in context.business_summary.lower()

    def test_translates_technical_language_in_executive_context(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        combined = _combined_context_text(context).lower()

        for term in _TECHNICAL_TERMS:
            assert term not in combined, f"Found technical term {term!r} in executive context"

    def test_avoids_repeating_analytical_telemetry(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        combined = _combined_context_text(context).lower()

        for phrase in _REPETITIVE_ANALYTICAL_PHRASES:
            assert phrase not in combined, f"Found repetitive analytical phrase {phrase!r}"

    def test_business_summary_communicates_significance(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert "operational analysis identified" not in context.business_summary.lower()
        assert context.business_summary.strip()
        assert (
            "outside normal expectations" in context.business_summary.lower()
            or "requires immediate review" in context.business_summary.lower()
            or "outside the normal operating range" in context.business_summary.lower()
            or "line b" in context.business_summary.lower()
        )

    def test_investigation_strategy_is_action_oriented(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        strategy = context.investigation_strategy.lower()

        assert "isolated" in strategy or "localised" in strategy or "localized" in strategy
        assert "production line" in strategy
        assert "data quality" in strategy or "operational causes" in strategy

    def test_investigation_categories_are_hypothesis_oriented(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert len(context.investigation_categories) >= 4
        assert any("data quality" in category for category in context.investigation_categories)

    def test_key_message_prefers_direct_answer(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert context.key_message
        assert "Line B" in context.key_message or "52" in context.key_message
        assert "materially outside normal expectations" not in context.key_message.lower()

    def test_assessment_confidence_is_present(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert context.assessment_confidence_level in {"High", "Medium", "Low"}
        assert context.assessment_confidence_rationale.strip()

    def test_why_this_matters_is_concise(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        combined = context.why_this_matters.lower()

        assert "avoid committing to irreversible" not in combined
        assert "reporting may not accurately reflect" not in combined or combined.count("reporting") <= 1

    def test_prioritized_explanations_use_evidence_framing(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert context.prioritized_explanations.startswith("Based on the available evidence")
        assert "hypothesis" in context.prioritized_explanations.lower()

    def test_recommended_actions_prefer_priority_actions(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())
        combined = " ".join(
            [*context.executive_actions, *context.operational_investigation_actions]
        ).lower()

        assert "inspect line b tooling" in combined
        assert "validate source data" not in combined

    def test_derives_investigation_targets_from_transparency_metadata(self) -> None:
        context = ExecutiveContextBuilder().build(_technical_request())

        assert context.investigation_targets == ("Production Line",)

    def test_handles_missing_dimension_metadata(self) -> None:
        snapshot = DeterministicAnalysisSnapshot(
            question="What changed?",
            direct_answer="Revenue increased.",
            executive_summary="Revenue increased.",
            analytical_findings=(),
            operational_assessment=None,
            executive_conclusions=(),
            priority_actions=(),
            transparency_summary=("Temporal filter: none applied.",),
            reasoning_trace=(),
            source_sections=("Direct Answer", "Executive Summary", "System Transparency"),
        )
        context = ExecutiveContextBuilder().build(NarrativeRequestBuilder().build(snapshot))

        assert context.investigation_targets == ()
        assert context.investigation_strategy

    def test_is_domain_agnostic(self) -> None:
        builder = ExecutiveContextBuilder()
        manufacturing = builder.build(_technical_request())
        education_snapshot = DeterministicAnalysisSnapshot(
            question="Which school has the lowest attendance?",
            direct_answer="School C: attendance_rate = 51 (z-score -5.61).",
            executive_summary="Operational analysis identified 1 finding(s): 0 high priority, 1 medium priority, and 0 low priority.",
            analytical_findings=("Attendance anomaly: School C is below peers.",),
            operational_assessment="high: Attendance requires review.",
            executive_conclusions=("Review School C attendance.",),
            priority_actions=("Contact School C leadership.",),
            transparency_summary=("Dimension: school",),
            reasoning_trace=("Theme 1: Attendance",),
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
        education = builder.build(NarrativeRequestBuilder().build(education_snapshot))

        assert manufacturing.investigation_targets == ("Production Line",)
        assert education.investigation_targets == ("School",)
        assert "manufacturing" not in " ".join(manufacturing.investigation_categories).lower()
        assert "education" not in " ".join(education.investigation_categories).lower()

    def test_builder_is_deterministic(self) -> None:
        request = _technical_request()
        builder = ExecutiveContextBuilder()

        assert builder.build(request) == builder.build(request)


_INTERNAL_NARRATIVE_TERMS = (
    "metric selected:",
    "aggregation inferred:",
    "comparison inferred:",
    "comparison direction inferred:",
    "routed tools:",
    "employee_name",
    "hayden king",
)


def _workforce_transparency_request() -> NarrativeRequest:
    snapshot = DeterministicAnalysisSnapshot(
        question="Which group has the highest values?",
        direct_answer="Hayden King has the highest Overtime Hours at 52.",
        executive_summary=(
            "Operational analysis identified 1 finding(s): 1 high priority, 0 medium priority, "
            "and 0 low priority."
        ),
        analytical_findings=(
            "Significant Variance Identified by Variance Analysis Tool: "
            "Hayden King overtime_hours is above peers.",
        ),
        operational_assessment="high: Overtime requires review.",
        executive_conclusions=("Review overtime concentration.",),
        priority_actions=("Validate overtime records for Hayden King.",),
        transparency_summary=(
            "Metric selected: Overtime Hours",
            "Dimension selected: employee_name",
            "Aggregation inferred: sum",
            "Comparison direction inferred: highest",
            "Dimension: employee_name",
            "Highest: Hayden King (52)",
            "Lowest: Sam Lee (8)",
        ),
        reasoning_trace=("Theme 1: overtime_hours",),
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
    return NarrativeRequestBuilder().build(snapshot)


class TestExecutiveNarrativeTranslationBoundaries:
    def test_executive_context_excludes_transparency_metadata(self) -> None:
        context = ExecutiveContextBuilder().build(_workforce_transparency_request())
        combined = _combined_context_text(context).lower()

        for term in _INTERNAL_NARRATIVE_TERMS:
            assert term not in combined, f"Found internal term {term!r} in executive context"

    def test_deterministic_narrative_excludes_transparency_metadata(self) -> None:
        artifact = PromptArtifactBuilder().build(_workforce_transparency_request())
        response = DeterministicNarrativeGenerator().generate(artifact)
        combined = "\n".join(section.content for section in response.sections).lower()

        for term in _INTERNAL_NARRATIVE_TERMS:
            assert term not in combined, f"Found internal term {term!r} in narrative sections"

    def test_person_names_are_abstracted_in_executive_context(self) -> None:
        context = ExecutiveContextBuilder().build(_workforce_transparency_request())
        combined = _combined_context_text(context)

        assert "Hayden King" not in combined
        assert "Individual employee" in combined or "Overtime Hours" in combined

    def test_operational_metric_labels_are_preserved(self) -> None:
        context = ExecutiveContextBuilder().build(_workforce_transparency_request())

        assert any("Overtime Hours" in metric for metric in context.affected_metrics)
        assert context.investigation_targets == ("Employee",)


class TestExecutiveContextPipelineIntegration:
    def test_prompt_artifact_includes_executive_context(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())

        assert artifact.executive_context == ExecutiveContextBuilder().build(_technical_request())

    def test_executive_evidence_excludes_transparency_telemetry(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())
        evidence_ids = {reference.evidence_id for reference in artifact.evidence_references}

        assert not any(evidence_id.startswith("transparency-") for evidence_id in evidence_ids)
        combined = " ".join(reference.content for reference in artifact.evidence_references).lower()
        assert "z-score" not in combined
        assert "operational analysis identified" not in combined

    def test_openai_formatter_uses_executive_context(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())
        user_message = OpenAIPromptFormatter().format(artifact)[1]["content"]

        assert "Executive context" in user_message
        assert "Investigation strategy:" in user_message
        assert "z-score" not in user_message.lower()
        assert "operational analysis identified" not in user_message.lower()

    def test_deterministic_generator_consumes_executive_context(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())
        response = DeterministicNarrativeGenerator().generate(artifact)
        combined = "\n".join(section.content for section in response.sections).lower()

        assert "z-score" not in combined
        assert "operational analysis identified" not in combined
        assert "production line" in combined
        assert "hypothes" in combined

    def test_deterministic_narrative_includes_assessment_confidence(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())
        response = DeterministicNarrativeGenerator().generate(artifact)
        key_message = response.sections[0].content

        assert "Assessment Confidence:" not in key_message
        assert response.assessment_confidence is not None
        assert response.assessment_confidence.level
        assert response.assessment_confidence.rationale

    def test_openai_generator_consumes_executive_context(self) -> None:
        artifact = PromptArtifactBuilder().build(_technical_request())
        fake_response = (
            "KEY MESSAGE:\n"
            "Defect concentration on Line B requires attention.\n\n"
            "WHY THIS MATTERS:\n"
            "Elevated defects may affect production commitments.\n\n"
            "WHERE TO INVESTIGATE FIRST:\n"
            "Compare defect rates across production lines.\n\n"
            "POSSIBLE EXPLANATIONS TO CHECK:\n"
            "Possible causes to check include tooling wear.\n\n"
            "EXECUTIVE ACTIONS:\n"
            "Validate source data before escalation.\n\n"
            "OPERATIONAL INVESTIGATION:\n"
            "Inspect Line B tooling.\n\n"
            "LIMITATIONS:\n"
            "Based only on supplied evidence."
        )
        messages = OpenAINarrativeGenerator(
            llm_client=FakeLLMClient(response=fake_response),
            config=OpenAIProviderConfig(model="gpt-4.1-mini"),
        ).generate(artifact)

        assert len(messages.sections) == 6
