import pandas as pd
from typing import List

from src.operational_intelligence.models import (
    AnalysisRequest,
    DatasetProfile,
    ToolResult,
    Finding,
)
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.trend_analysis import TrendAnalysisTool
from src.operational_intelligence.variance_analysis import VarianceAnalysisTool
from src.operational_intelligence.anomaly_detection import AnomalyDetectionTool
from src.operational_intelligence.risk_assessment import RiskAssessmentTool


IDENTIFIER_COLUMNS = {
    "employee_id",
    "employee_number",
    "record_id",
    "transaction_id",
    "id",
    "uuid",
}


def _is_identifier_column(column_name: str) -> bool:
    lowered = column_name.strip().lower()
    if lowered in IDENTIFIER_COLUMNS:
        return True
    if lowered.endswith("_id") or lowered.endswith("_number"):
        return True
    return False


def _non_identifier_dimensions(potential_dimensions: list[str]) -> list[str]:
    return [
        dimension
        for dimension in potential_dimensions
        if not _is_identifier_column(dimension)
    ]


def _select_dimension_from_question(
    question: str,
    potential_dimensions: list[str],
) -> str | None:
    question_lower = question.lower()
    matched = [
        dimension
        for dimension in potential_dimensions
        if dimension.lower() in question_lower
    ]
    if not matched:
        return None
    return max(matched, key=len)


def _select_variance_dimension(
    question: str,
    potential_dimensions: list[str],
) -> str:
    explicit_dimension = _select_dimension_from_question(question, potential_dimensions)
    if explicit_dimension is not None:
        return explicit_dimension

    non_identifier_dimensions = _non_identifier_dimensions(potential_dimensions)
    if non_identifier_dimensions:
        return non_identifier_dimensions[0]

    return potential_dimensions[0]


def _select_metric_from_question(
    question: str,
    potential_metrics: list[str],
) -> str | None:
    question_lower = question.lower()
    matched = [
        metric
        for metric in potential_metrics
        if metric.lower() in question_lower
    ]
    if not matched:
        return None
    return max(matched, key=len)


class OperationalPipeline:
    """
    Coordinates intent routing, analysis tool execution, and risk assessment workflow.
    """

    def __init__(self):
        self.intent_router = IntentRouter()
        self.trend_tool = TrendAnalysisTool()
        self.variance_tool = VarianceAnalysisTool()
        self.anomaly_tool = AnomalyDetectionTool()
        self.risk_tool = RiskAssessmentTool()

    def run(
        self,
        request: AnalysisRequest,
        df: pd.DataFrame,
        dataset_profiles: List[DatasetProfile],
    ) -> List[Finding]:
        """
        Execute the operational intelligence pipeline for a single AnalysisRequest.

        Args:
            request: The analysis request with question/context.
            df: DataFrame containing the dataset to analyze.
            dataset_profiles: List of profiles for available datasets.

        Returns:
            List of Finding objects produced by risk assessment, or empty if nothing actionable.
        """
        # Basic input validation
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an instance of AnalysisRequest")
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("df must be a non-empty pandas DataFrame")
        if not isinstance(dataset_profiles, list) or not dataset_profiles:
            raise ValueError("dataset_profiles must be a non-empty list of DatasetProfile")
        
        profile = dataset_profiles[0]
        tool_names = self.intent_router.route(request, dataset_profiles)
        tool_results: List[ToolResult] = []

        for tool_name in tool_names:
            if tool_name == "trend_analysis":
                date_cols = getattr(profile, "date_columns", None)
                metrics = getattr(profile, "potential_metrics", None)
                if not date_cols or not isinstance(date_cols, list) or not date_cols:
                    tool_results.append(ToolResult(
                        tool_name="trend_analysis",
                        success=False,
                        summary="Trend analysis could not run: No date columns available in profile.",
                        evidence_items=[],
                        warnings=["Profile lacks date_columns required for trend analysis."]
                    ))
                    continue
                if not metrics or not isinstance(metrics, list) or not metrics:
                    tool_results.append(ToolResult(
                        tool_name="trend_analysis",
                        success=False,
                        summary="Trend analysis could not run: No potential metrics available in profile.",
                        evidence_items=[],
                        warnings=["Profile lacks potential_metrics required for trend analysis."]
                    ))
                    continue
                date_col = date_cols[0]
                metric_col = metrics[0]
                try:
                    result = self.trend_tool.analyze(df, date_col, metric_col)
                except Exception as ex:
                    tool_results.append(ToolResult(
                        tool_name="trend_analysis",
                        success=False,
                        summary=f"Trend analysis failed: {str(ex)}",
                        evidence_items=[],
                        warnings=[f"Exception during trend analysis: {str(ex)}"]
                    ))
                else:
                    tool_results.append(result)

            elif tool_name == "variance_analysis":
                dims = getattr(profile, "potential_dimensions", None)
                metrics = getattr(profile, "potential_metrics", None)
                if not dims or not isinstance(dims, list) or not dims:
                    tool_results.append(ToolResult(
                        tool_name="variance_analysis",
                        success=False,
                        summary="Variance analysis could not run: No potential dimensions available in profile.",
                        evidence_items=[],
                        warnings=["Profile lacks potential_dimensions required for variance analysis."]
                    ))
                    continue
                if not metrics or not isinstance(metrics, list) or not metrics:
                    tool_results.append(ToolResult(
                        tool_name="variance_analysis",
                        success=False,
                        summary="Variance analysis could not run: No potential metrics available in profile.",
                        evidence_items=[],
                        warnings=["Profile lacks potential_metrics required for variance analysis."]
                    ))
                    continue
                dimension_col = _select_variance_dimension(request.question, dims)

                metric_col = _select_metric_from_question(request.question, metrics)
                if metric_col is None:
                    metric_col = metrics[0]
                try:
                    result = self.variance_tool.analyze(df, dimension_col, metric_col)
                except Exception as ex:
                    tool_results.append(ToolResult(
                        tool_name="variance_analysis",
                        success=False,
                        summary=f"Variance analysis failed: {str(ex)}",
                        evidence_items=[],
                        warnings=[f"Exception during variance analysis: {str(ex)}"]
                    ))
                else:
                    tool_results.append(result)
                
            elif tool_name == "anomaly_detection":
                metrics = getattr(profile, "potential_metrics", None)
                if not metrics or not isinstance(metrics, list) or not metrics:
                    tool_results.append(ToolResult(
                        tool_name="anomaly_detection",
                        success=False,
                        summary="Anomaly detection could not run: No potential metrics available in profile.",
                        evidence_items=[],
                        warnings=["Profile lacks potential_metrics required for anomaly detection."]
                    ))
                    continue
                metric_col = metrics[0]
                try:
                    result = self.anomaly_tool.analyze(df, metric_col, threshold=1.5)
                except Exception as ex:
                    tool_results.append(ToolResult(
                        tool_name="anomaly_detection",
                        success=False,
                        summary=f"Anomaly detection failed: {str(ex)}",
                        evidence_items=[],
                        warnings=[f"Exception during anomaly detection: {str(ex)}"]
                    ))
                else:
                    tool_results.append(result)

            elif tool_name == "risk_assessment":
                # RiskAssessment is run after analysis toolresults gathered, not directly here.
                continue

        # If no tool results from analysis tools, return an empty findings list
        analysis_results = [
            t for t in tool_results
            if getattr(t, "tool_name", "") != "risk_assessment"
        ]
        if not analysis_results:
            return []

        findings = self.risk_tool.assess(analysis_results)
        return findings