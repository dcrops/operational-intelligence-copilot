from dataclasses import dataclass, field

from src.operational_intelligence.models import (
    AnalysisRequest,
    ClarificationRequest,
    ExecutiveReport,
    Finding,
    SnapshotContext,
    TemporalFilterContext,
)


@dataclass
class AnalysisResult:
    """UI bundle produced by a single analysis run."""

    request: AnalysisRequest
    routes: list[str]
    findings: list[Finding]
    report: ExecutiveReport | None
    direct_answer: str
    deterministic_answer: str
    clarification: ClarificationRequest | None = None
    metrics_analysed: list[str] = field(default_factory=list)
    temporal_filter: TemporalFilterContext | None = None
    snapshot_context: SnapshotContext | None = None
