from dataclasses import dataclass

from src.operational_intelligence.models import (
    AnalysisRequest,
    ExecutiveReport,
    Finding,
)


@dataclass
class AnalysisResult:
    """UI bundle produced by a single analysis run."""

    request: AnalysisRequest
    routes: list[str]
    findings: list[Finding]
    report: ExecutiveReport
    deterministic_answer: str
