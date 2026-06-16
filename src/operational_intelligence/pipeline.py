import pandas as pd
from typing import List, Union

from src.operational_intelligence.models import (
    AnalysisRequest,
    ClarificationRequest,
    DatasetProfile,
    ToolResult,
    Finding,
)
from src.operational_intelligence.intent_router import IntentRouter
from src.operational_intelligence.ambiguity_detection import detect_clarification
from src.operational_intelligence.schema_resolution import (
    non_identifier_dimensions,
    resolve_metric_from_question,
    resolve_dimension_from_question,
)
from src.operational_intelligence.question_semantics import (
    ComparisonDirection,
    infer_aggregation_type,
    resolve_comparison_direction,
)
from src.operational_intelligence.trend_analysis import TrendAnalysisTool
from src.operational_intelligence.variance_analysis import VarianceAnalysisTool
from src.operational_intelligence.anomaly_detection import AnomalyDetectionTool
from src.operational_intelligence.risk_assessment import RiskAssessmentTool


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
    ) -> Union[ClarificationRequest, List[Finding]]:
        if not isinstance(request, AnalysisRequest):
            raise ValueError("request must be an instance of AnalysisRequest")
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("df must be a non-empty pandas DataFrame")
        if not isinstance(dataset_profiles, list) or not dataset_profiles:
            raise ValueError("dataset_profiles must be a non-empty list of DatasetProfile")
        
        profile = dataset_profiles[0]
        tool_names = self.intent_router.route(request, dataset_profiles)

        clarification = detect_clarification(request, tool_names, profile)
        if clarification is not None:
            return clarification

        comparison_direction = self._resolve_comparison_direction(request)
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
                metric_col = self._resolve_metric(request, metrics)
                aggregation = infer_aggregation_type(metric_col)
                try:
                    result = self.trend_tool.analyze(
                        df,
                        date_col,
                        metric_col,
                        aggregation=aggregation,
                    )
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
                dimension_col = self._resolve_variance_dimension(request, dims)
                metric_col = self._resolve_metric(request, metrics)
                aggregation = infer_aggregation_type(metric_col)
                try:
                    result = self.variance_tool.analyze(
                        df,
                        dimension_col,
                        metric_col,
                        aggregation=aggregation,
                        comparison_direction=comparison_direction,
                    )
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

                metrics_to_analyze = self._resolve_anomaly_metrics(request, metrics)
                for metric_col in metrics_to_analyze:
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
                continue

        analysis_results = [
            t for t in tool_results
            if getattr(t, "tool_name", "") != "risk_assessment"
        ]
        if not analysis_results:
            return []

        findings = self.risk_tool.assess(analysis_results)
        return findings

    @staticmethod
    def _resolve_comparison_direction(request: AnalysisRequest) -> ComparisonDirection:
        selected = request.selected_comparison_direction
        if selected in {"top", "bottom", "dual"}:
            return selected

        resolved = resolve_comparison_direction(request.question)
        if resolved is not None:
            return resolved
        return "top"

    @staticmethod
    def _resolve_metric(request: AnalysisRequest, metrics: list[str]) -> str:
        if request.selected_metrics:
            return request.selected_metrics[0]

        metric_col = resolve_metric_from_question(request.question, metrics)
        if metric_col is not None:
            return metric_col

        if len(metrics) == 1:
            return metrics[0]

        raise ValueError(
            "Metric could not be resolved from the question. Clarification should have been requested."
        )

    @staticmethod
    def _resolve_variance_dimension(request: AnalysisRequest, dimensions: list[str]) -> str:
        if request.selected_dimensions:
            return request.selected_dimensions[0]

        dimension_col = resolve_dimension_from_question(request.question, dimensions)
        if dimension_col is not None:
            return dimension_col

        fallback_dimensions = non_identifier_dimensions(dimensions)
        if len(fallback_dimensions) == 1:
            return fallback_dimensions[0]

        raise ValueError(
            "Dimension could not be resolved from the question. Clarification should have been requested."
        )

    @staticmethod
    def _resolve_anomaly_metrics(request: AnalysisRequest, metrics: list[str]) -> list[str]:
        if request.selected_metrics:
            return list(request.selected_metrics)

        metric_col = resolve_metric_from_question(request.question, metrics)
        if metric_col is not None:
            return [metric_col]

        return list(metrics)
