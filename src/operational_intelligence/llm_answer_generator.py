"""Legacy LLM answer generator superseded by the Phase 4 narrative boundary.

This module predates Milestone 11a. Do not wire it into new Phase 4 work.
Use ``src.operational_intelligence.llm`` narrative types
(``NarrativeRequestBuilder``, ``NarrativeGenerator``, ``DeterministicNarrativeGenerator``)
instead. Real LLM integration belongs behind the narrative boundary in later milestones.
"""

from src.operational_intelligence.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.operational_intelligence.llm.protocol import LLMClient
from src.operational_intelligence.models import AnalysisRequest, ExecutiveReport, Finding


class LLMAnswerGenerator:
    """
    Generates a user-facing answer by explaining structured analysis results via an LLM.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def generate(
        self,
        request: AnalysisRequest,
        findings: list[Finding],
        report: ExecutiveReport,
    ) -> str:
        """
        Produce a natural-language answer grounded in pre-computed findings and report data.
        """
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an AnalysisRequest")
        if not isinstance(findings, list):
            raise ValueError("findings must be a list")
        if not isinstance(report, ExecutiveReport):
            raise ValueError("report must be an ExecutiveReport")

        if not findings:
            return "No findings were identified from the analysis."

        request_data = request.model_dump()
        findings_data = [finding.model_dump() for finding in findings]
        report_data = report.model_dump()

        user_prompt = build_user_prompt(
            question=request.question,
            request_data=request_data,
            findings_data=findings_data,
            report_data=report_data,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        return self._llm_client.complete(messages, temperature=0.0)
