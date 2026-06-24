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
