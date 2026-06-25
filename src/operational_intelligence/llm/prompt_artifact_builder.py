"""Pure transformer from narrative requests to vendor-neutral prompt artifacts."""

from __future__ import annotations

from src.operational_intelligence.llm.executive_context_builder import ExecutiveContextBuilder
from src.operational_intelligence.llm.narrative_governance import (
    DEFAULT_NARRATIVE_OBJECTIVE,
    OBJECTIVE_INSTRUCTIONS,
    PROMPT_ARTIFACT_VERSION,
    PROHIBITED_BEHAVIOURS,
    SECTION_ANALYTICAL_FINDINGS,
    SECTION_DIRECT_ANSWER,
    SECTION_EXECUTIVE_CONCLUSIONS,
    SECTION_EXECUTIVE_SUMMARY,
    SECTION_OPERATIONAL_ASSESSMENT,
    SECTION_PRIORITY_ACTIONS,
    SUPPORTED_NARRATIVE_OBJECTIVES,
    SYSTEM_INSTRUCTIONS,
)
from src.operational_intelligence.llm.narrative_models import (
    EvidenceReference,
    ExecutiveContext,
    GroundingConstraints,
    NarrativeRequest,
    PromptArtifact,
)


class PromptArtifactBuilder:
    """Build prompt artifacts from completed narrative requests."""

    def __init__(
        self,
        *,
        executive_context_builder: ExecutiveContextBuilder | None = None,
    ) -> None:
        self._executive_context_builder = (
            executive_context_builder or ExecutiveContextBuilder()
        )

    def build(
        self,
        request: NarrativeRequest,
        *,
        narrative_objective: str | None = None,
    ) -> PromptArtifact:
        """Return a read-only prompt artifact without analytics or mutation."""
        objective = narrative_objective or DEFAULT_NARRATIVE_OBJECTIVE
        if objective not in SUPPORTED_NARRATIVE_OBJECTIVES:
            raise ValueError(f"Unsupported narrative objective: {objective}")

        executive_context = self._executive_context_builder.build(request)
        evidence_references = self._build_executive_evidence_references(executive_context)
        system_instructions = SYSTEM_INSTRUCTIONS + OBJECTIVE_INSTRUCTIONS[objective]
        grounding_constraints = GroundingConstraints(
            closed_world=True,
            allowed_source_sections=request.source_sections,
            prohibited_behaviours=PROHIBITED_BEHAVIOURS,
        )

        return PromptArtifact(
            artifact_version=PROMPT_ARTIFACT_VERSION,
            narrative_objective=objective,
            system_instructions=system_instructions,
            question=request.question,
            direct_answer=request.direct_answer,
            executive_summary=request.executive_summary,
            analytical_findings=request.analytical_findings,
            operational_assessment=request.operational_assessment,
            executive_conclusions=request.executive_conclusions,
            priority_actions=request.priority_actions,
            transparency_summary=request.transparency_summary,
            reasoning_trace=request.reasoning_trace,
            source_sections=request.source_sections,
            evidence_references=evidence_references,
            executive_context=executive_context,
            grounding_constraints=grounding_constraints,
        )

    def _build_executive_evidence_references(
        self,
        context: ExecutiveContext,
    ) -> tuple[EvidenceReference, ...]:
        references: list[EvidenceReference] = []

        references.append(
            EvidenceReference(
                evidence_id="direct-answer",
                section=SECTION_DIRECT_ANSWER,
                label="Direct Answer",
                content=context.direct_answer_summary,
            )
        )
        references.append(
            EvidenceReference(
                evidence_id="executive-summary",
                section=SECTION_EXECUTIVE_SUMMARY,
                label="Executive Summary",
                content=context.business_summary,
            )
        )
        references.append(
            EvidenceReference(
                evidence_id="key-message",
                section=SECTION_EXECUTIVE_SUMMARY,
                label="Key Message",
                content=context.key_message,
            )
        )
        references.append(
            EvidenceReference(
                evidence_id="assessment-confidence",
                section=SECTION_EXECUTIVE_SUMMARY,
                label="Assessment Confidence",
                content=(
                    f"{context.assessment_confidence_level}: "
                    f"{context.assessment_confidence_rationale}"
                ),
            )
        )
        references.append(
            EvidenceReference(
                evidence_id="executive-assessment",
                section=SECTION_OPERATIONAL_ASSESSMENT,
                label="Executive Assessment",
                content=context.executive_assessment_headline,
            )
        )

        for index, finding in enumerate(context.key_findings, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"finding-{index}",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label=f"Business Implication {index}",
                    content=finding,
                )
            )

        if context.business_impact:
            references.append(
                EvidenceReference(
                    evidence_id="business-impact",
                    section=SECTION_EXECUTIVE_SUMMARY,
                    label="Business Impact",
                    content=context.business_impact,
                )
            )

        if context.decision_guidance:
            references.append(
                EvidenceReference(
                    evidence_id="decision-guidance",
                    section=SECTION_OPERATIONAL_ASSESSMENT,
                    label="Decision Guidance",
                    content=context.decision_guidance,
                )
            )

        if context.investigation_strategy:
            references.append(
                EvidenceReference(
                    evidence_id="investigation-strategy",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label="Investigation Strategy",
                    content=context.investigation_strategy,
                )
            )

        if context.prioritized_explanations:
            references.append(
                EvidenceReference(
                    evidence_id="prioritized-explanations",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label="Prioritized Explanations",
                    content=context.prioritized_explanations,
                )
            )

        if context.why_this_matters:
            references.append(
                EvidenceReference(
                    evidence_id="why-this-matters",
                    section=SECTION_EXECUTIVE_SUMMARY,
                    label="Why This Matters",
                    content=context.why_this_matters,
                )
            )

        if context.operational_significance or context.executive_severity:
            assessment_parts: list[str] = []
            if context.executive_severity:
                assessment_parts.append(f"Severity: {context.executive_severity}")
            if context.operational_significance:
                assessment_parts.append(context.operational_significance)
            references.append(
                EvidenceReference(
                    evidence_id="operational-assessment",
                    section=SECTION_OPERATIONAL_ASSESSMENT,
                    label="Operational Assessment",
                    content=". ".join(assessment_parts),
                )
            )

        for index, conclusion in enumerate(context.conclusions, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"conclusion-{index}",
                    section=SECTION_EXECUTIVE_CONCLUSIONS,
                    label=f"Conclusion {index}",
                    content=conclusion,
                )
            )

        for index, action in enumerate(context.executive_actions, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"executive-action-{index}",
                    section=SECTION_PRIORITY_ACTIONS,
                    label=f"Executive Action {index}",
                    content=action,
                )
            )

        for index, action in enumerate(context.operational_investigation_actions, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"operational-action-{index}",
                    section=SECTION_PRIORITY_ACTIONS,
                    label=f"Operational Investigation {index}",
                    content=action,
                )
            )

        if context.investigation_targets:
            references.append(
                EvidenceReference(
                    evidence_id="investigation-targets",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label="Investigation Targets",
                    content=", ".join(context.investigation_targets),
                )
            )

        if context.investigation_categories:
            references.append(
                EvidenceReference(
                    evidence_id="investigation-categories",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label="Investigation Categories",
                    content="; ".join(context.investigation_categories),
                )
            )

        if context.affected_metrics:
            references.append(
                EvidenceReference(
                    evidence_id="affected-metrics",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label="Affected Metrics",
                    content=", ".join(context.affected_metrics),
                )
            )

        return tuple(references)
