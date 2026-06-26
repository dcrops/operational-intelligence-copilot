from dataclasses import dataclass, field
from datetime import datetime

from src.operational_intelligence.llm.narrative_config import NarrativeRuntimeConfig
from src.operational_intelligence.llm.narrative_models import NarrativeResponse
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
    narrative: NarrativeResponse | None = None
    narrative_warnings: tuple[str, ...] = field(default_factory=tuple)
    completed_at: datetime | None = None
