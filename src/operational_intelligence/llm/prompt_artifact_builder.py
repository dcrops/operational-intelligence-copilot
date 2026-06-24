"""Pure transformer from narrative requests to vendor-neutral prompt artifacts."""

from __future__ import annotations

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
    SECTION_SYSTEM_TRANSPARENCY,
    SUPPORTED_NARRATIVE_OBJECTIVES,
    SYSTEM_INSTRUCTIONS,
)
from src.operational_intelligence.llm.narrative_models import (
    EvidenceReference,
    GroundingConstraints,
    NarrativeRequest,
    PromptArtifact,
)


def _split_finding_summary(summary: str) -> tuple[str, str]:
    if ": " in summary:
        title, description = summary.split(": ", 1)
        return title, description
    return summary, summary


class PromptArtifactBuilder:
    """Build prompt artifacts from completed narrative requests."""

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

        evidence_references = self._build_evidence_references(request)
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
            grounding_constraints=grounding_constraints,
        )

    def _build_evidence_references(
        self,
        request: NarrativeRequest,
    ) -> tuple[EvidenceReference, ...]:
        references: list[EvidenceReference] = []

        references.append(
            EvidenceReference(
                evidence_id="direct-answer",
                section=SECTION_DIRECT_ANSWER,
                label="Direct Answer",
                content=request.direct_answer,
            )
        )
        references.append(
            EvidenceReference(
                evidence_id="executive-summary",
                section=SECTION_EXECUTIVE_SUMMARY,
                label="Executive Summary",
                content=request.executive_summary,
            )
        )

        for index, finding in enumerate(request.analytical_findings, start=1):
            label, content = _split_finding_summary(finding)
            references.append(
                EvidenceReference(
                    evidence_id=f"finding-{index}",
                    section=SECTION_ANALYTICAL_FINDINGS,
                    label=label,
                    content=content,
                )
            )

        if request.operational_assessment:
            references.append(
                EvidenceReference(
                    evidence_id="operational-assessment",
                    section=SECTION_OPERATIONAL_ASSESSMENT,
                    label="Operational Assessment",
                    content=request.operational_assessment,
                )
            )

        for index, conclusion in enumerate(request.executive_conclusions, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"conclusion-{index}",
                    section=SECTION_EXECUTIVE_CONCLUSIONS,
                    label=f"Conclusion {index}",
                    content=conclusion,
                )
            )

        for index, action in enumerate(request.priority_actions, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"action-{index}",
                    section=SECTION_PRIORITY_ACTIONS,
                    label=f"Priority Action {index}",
                    content=action,
                )
            )

        for index, line in enumerate(request.transparency_summary, start=1):
            references.append(
                EvidenceReference(
                    evidence_id=f"transparency-{index}",
                    section=SECTION_SYSTEM_TRANSPARENCY,
                    label=f"Transparency {index}",
                    content=line,
                )
            )

        return tuple(references)
