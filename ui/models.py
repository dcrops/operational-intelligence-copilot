from dataclasses import dataclass

from src.operational_intelligence.models import (
    AnalysisRequest,
    ClarificationRequest,
    ExecutiveReport,
    Finding,
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
