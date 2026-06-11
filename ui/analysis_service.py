import pandas as pd

from src.operational_intelligence.answer_generator import AnswerGenerator
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.models import AnalysisRequest, DatasetProfile
from src.operational_intelligence.pipeline import OperationalPipeline
from src.operational_intelligence.reporting import ExecutiveReportGenerator
from ui.models import AnalysisResult


def run_analysis(
    question: str,
    df: pd.DataFrame,
    profile: DatasetProfile,
) -> AnalysisResult:
    """
    Run the operational intelligence flow for a natural language question.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Please enter a question before running analysis.")

    request = AnalysisRequest(
        question=cleaned_question,
        dataset_names=[profile.dataset_name],
    )

    routes = IntentRouter().route(request, [profile])
    findings = OperationalPipeline().run(request, df, [profile])
    report = ExecutiveReportGenerator().generate(findings)
    deterministic_answer = AnswerGenerator().generate(request, findings, report)

    return AnalysisResult(
        request=request,
        routes=routes,
        findings=findings,
        report=report,
        deterministic_answer=deterministic_answer,
    )
