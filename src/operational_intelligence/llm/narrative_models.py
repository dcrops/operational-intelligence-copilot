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
class NarrativeResponse:
    """Communication output from narrative generation only."""

    executive_narrative: str
    key_message: str
    limitations: str
    source_sections_used: tuple[str, ...]
    generator_type: str


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
    grounding_constraints: GroundingConstraints
