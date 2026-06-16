from typing import List

from src.operational_intelligence.models import AnalysisRequest, DatasetProfile
from src.operational_intelligence.question_semantics import (
    has_anomaly_intent,
    has_comparative_intent,
    has_risk_intent,
    has_trend_intent,
    requests_dual_analysis_outcomes,
)


class IntentRouter:
    """
    Routes natural language analysis questions to the appropriate operational intelligence tools.
    """

    TOOL_ORDER = [
        "trend_analysis",
        "variance_analysis",
        "anomaly_detection",
        "risk_assessment",
    ]

    def route(
        self,
        request: AnalysisRequest,
        dataset_profiles: List[DatasetProfile],
    ) -> List[str]:
        """
        Determines which analysis tools to route the natural language request to.
        """
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an instance of AnalysisRequest")
        if not isinstance(dataset_profiles, list) or not dataset_profiles:
            raise ValueError("dataset_profiles must be a non-empty list of DatasetProfile objects")

        analysis_type = getattr(request, "requested_analysis_type", None)
        if analysis_type:
            if isinstance(analysis_type, str):
                return [analysis_type]
            raise ValueError("requested_analysis_type must be a string if provided")

        question = getattr(request, "question", None)
        if not isinstance(question, str) or not question.strip():
            raise ValueError("request must have a non-empty 'question' string")

        comparative = has_comparative_intent(question)
        anomaly = has_anomaly_intent(question)
        trend = has_trend_intent(question)
        risk = has_risk_intent(question)

        selected_tools: list[str] = []

        if comparative and anomaly:
            if requests_dual_analysis_outcomes(question):
                selected_tools.extend(["variance_analysis", "anomaly_detection"])
            else:
                selected_tools.extend(["variance_analysis", "anomaly_detection"])
        elif comparative:
            selected_tools.append("variance_analysis")
        elif anomaly:
            selected_tools.append("anomaly_detection")
        elif trend:
            selected_tools.append("trend_analysis")

        if risk:
            selected_tools.append("risk_assessment")

        if selected_tools:
            return [tool for tool in self.TOOL_ORDER if tool in selected_tools]

        suitable_tools: list[str] = []
        for profile in dataset_profiles:
            tools = getattr(profile, "suitable_tools", None)
            if isinstance(tools, list):
                suitable_tools.extend(str(tool) for tool in tools if tool)

        deduped_tools: list[str] = []
        for tool in self.TOOL_ORDER:
            if tool in suitable_tools and tool not in deduped_tools:
                deduped_tools.append(tool)

        if not deduped_tools:
            raise ValueError("No suitable tools found for routing the request")

        return deduped_tools
