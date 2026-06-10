from typing import List
from src.operational_intelligence.models import AnalysisRequest, DatasetProfile

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

    _TREND_KEYWORDS = [
        "trend", "over time", "changed", "increase", "decrease", "monthly", "weekly"
    ]
    _VARIANCE_KEYWORDS = [
        "compare", "highest", "lowest", "by department", "by group", "difference", "variance"
    ]
    _ANOMALY_KEYWORDS = [
        "anomaly", "unusual", "outlier", "spike", "abnormal"
    ]
    _RISK_KEYWORDS = [
        "risk", "investigate", "concern", "issue", "problem", "review"
    ]

    def route(
        self,
        request: AnalysisRequest,
        dataset_profiles: List[DatasetProfile],
    ) -> List[str]:
        """
        Determines which analysis tools to route the natural language request to.

        Args:
            request: The analysis request to route.
            dataset_profiles: List of DatasetProfile objects.

        Returns:
            List of tool names (str) in sensible execution order.

        Raises:
            ValueError: If arguments are invalid.
        """
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an instance of AnalysisRequest")
        if not isinstance(dataset_profiles, list) or not dataset_profiles:
            raise ValueError("dataset_profiles must be a non-empty list of DatasetProfile objects")

        # If analysis type is explicitly provided, use it directly
        analysis_type = getattr(request, "requested_analysis_type", None)
        if analysis_type:
            if isinstance(analysis_type, str):
                return [analysis_type]
            raise ValueError("requested_analysis_type must be a string if provided")

        # Otherwise, derive from question
        question = getattr(request, "question", None)
        if not isinstance(question, str) or not question.strip():
            raise ValueError("request must have a non-empty 'question' string")

        q = question.lower()
        selected_tools = []

        # Helper for matching any keyword in question
        def contains_keywords(keywords: List[str]) -> bool:
            return any(keyword in q for keyword in keywords)

        if contains_keywords(self._TREND_KEYWORDS):
            selected_tools.append("trend_analysis")
        if contains_keywords(self._VARIANCE_KEYWORDS):
            selected_tools.append("variance_analysis")
        if contains_keywords(self._ANOMALY_KEYWORDS):
            selected_tools.append("anomaly_detection")
        if contains_keywords(self._RISK_KEYWORDS):
            selected_tools.append("risk_assessment")

        # If any criteria were matched, return those (de-duped, respecting TOOL_ORDER)
        if selected_tools:
            # Ensure order and deduplication
            ordered = [tool for tool in self.TOOL_ORDER if tool in selected_tools]
            return ordered

        # If nothing matched, fall back to tool suggestions from dataset profiles
        suitable_tools = []
        for profile in dataset_profiles:
            tools = getattr(profile, "suitable_tools", None)
            if isinstance(tools, list):
                suitable_tools.extend(str(t) for t in tools if t)

        # Deduplicate and preserve intended order
        deduped_tools = []
        for tool in self.TOOL_ORDER:
            if tool in suitable_tools and tool not in deduped_tools:
                deduped_tools.append(tool)

        if not deduped_tools:
            raise ValueError("No suitable tools found for routing the request")

        return deduped_tools