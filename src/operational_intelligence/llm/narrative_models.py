"""Frozen models for the AI narrative integration boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeterministicAnalysisSnapshot:
    """Read-only deterministic analysis output consumed by the narrative layer."""

    question: str
    direct_answer: str
    executive_summary: str
    analytical_findings: tuple[str, ...]
    operational_assessment: str | None
    executive_conclusions: tuple[str, ...]
    priority_actions: tuple[str, ...]
    transparency_summary: tuple[str, ...]
    reasoning_trace: tuple[str, ...]
    source_sections: tuple[str, ...]


@dataclass(frozen=True)
class NarrativeRequest:
    """Deterministic input for narrative generation only."""

    question: str
    direct_answer: str
    executive_summary: str
    analytical_findings: tuple[str, ...]
    operational_assessment: str | None
    executive_conclusions: tuple[str, ...]
    priority_actions: tuple[str, ...]
    transparency_summary: tuple[str, ...]
    reasoning_trace: tuple[str, ...]
    source_sections: tuple[str, ...]


@dataclass(frozen=True)
class ExecutiveAssessmentBanner:
    """Deterministic executive assessment banner for narrative presentation."""

    level: str
    indicator: str
    headline: str


@dataclass(frozen=True)
class AssessmentConfidencePresentation:
    """Structured assessment confidence for narrative presentation."""

    level: str
    indicator: str
    rationale: str


@dataclass(frozen=True)
class ExecutiveContext:
    """Business-level context translated from deterministic analysis."""

    question: str
    key_message: str
    executive_assessment_level: str
    executive_assessment_indicator: str
    executive_assessment_headline: str
    assessment_confidence_level: str
    assessment_confidence_rationale: str
    business_summary: str
    direct_answer_summary: str
    why_this_matters: str
    key_findings: tuple[str, ...]
    operational_significance: str | None
    executive_severity: str | None
    business_impact: str | None
    decision_guidance: str | None
    investigation_strategy: str
    prioritized_explanations: str
    conclusions: tuple[str, ...]
    executive_actions: tuple[str, ...]
    operational_investigation_actions: tuple[str, ...]
    investigation_targets: tuple[str, ...]
    investigation_categories: tuple[str, ...]
    affected_metrics: tuple[str, ...]


@dataclass(frozen=True)
class NarrativeSection:
    """Reusable narrative section for executive communication output."""

    title: str
    content: str


@dataclass(frozen=True)
class NarrativeResponse:
    """Communication output from narrative generation only."""

    sections: tuple[NarrativeSection, ...]
    limitations: str
    source_sections_used: tuple[str, ...]
    generator_type: str
    executive_assessment: ExecutiveAssessmentBanner | None = None
    assessment_confidence: AssessmentConfidencePresentation | None = None
    model: str | None = None
    generation_duration_ms: int | None = None
    artifact_version: str | None = None


@dataclass(frozen=True)
class EvidenceReference:
    """Traceable deterministic evidence for future AI narratives."""

    evidence_id: str
    section: str
    label: str
    content: str
    severity: str | None = None


@dataclass(frozen=True)
class GroundingConstraints:
    """Governance rules encoded into the prompt artifact."""

    closed_world: bool
    allowed_source_sections: tuple[str, ...]
    prohibited_behaviours: tuple[str, ...]


@dataclass(frozen=True)
class PromptArtifact:
    """Vendor-neutral, AI-ready representation of deterministic evidence."""

    artifact_version: str
    narrative_objective: str
    system_instructions: tuple[str, ...]
    question: str
    direct_answer: str
    executive_summary: str
    analytical_findings: tuple[str, ...]
    operational_assessment: str | None
    executive_conclusions: tuple[str, ...]
    priority_actions: tuple[str, ...]
    transparency_summary: tuple[str, ...]
    reasoning_trace: tuple[str, ...]
    source_sections: tuple[str, ...]
    evidence_references: tuple[EvidenceReference, ...]
    executive_context: ExecutiveContext
    grounding_constraints: GroundingConstraints
