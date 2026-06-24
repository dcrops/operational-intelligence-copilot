"""Pure transformer from deterministic analysis snapshots to narrative requests."""

from __future__ import annotations

from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    NarrativeRequest,
)


class NarrativeRequestBuilder:
    """Build narrative requests from completed deterministic analysis output."""

    def build(self, snapshot: DeterministicAnalysisSnapshot) -> NarrativeRequest:
        """Return a read-only narrative request without analytics or mutation."""
        return NarrativeRequest(
            question=snapshot.question,
            direct_answer=snapshot.direct_answer,
            executive_summary=snapshot.executive_summary,
            analytical_findings=snapshot.analytical_findings,
            operational_assessment=snapshot.operational_assessment,
            executive_conclusions=snapshot.executive_conclusions,
            priority_actions=snapshot.priority_actions,
            transparency_summary=snapshot.transparency_summary,
            reasoning_trace=snapshot.reasoning_trace,
            source_sections=snapshot.source_sections,
        )
