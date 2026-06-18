from pydantic import BaseModel, Field, field_validator

class DatasetProfile(BaseModel):
    """
    Profile describing a dataset's basic structure and profiling stats.
    """
    dataset_name: str = Field(..., description="Unique name of the dataset.")
    row_count: int = Field(..., description="Total number of rows in the dataset.")
    column_count: int = Field(..., description="Total number of columns in the dataset.")
    column_names: list[str] = Field(default_factory=list, description="List of all column names.")
    numeric_columns: list[str] = Field(default_factory=list, description="List of columns inferred as numeric.")
    categorical_columns: list[str] = Field(default_factory=list, description="List of columns inferred as categorical.")
    date_columns: list[str] = Field(default_factory=list, description="List of columns inferred as date/time.")
    missing_value_count: int = Field(..., description="Total number of missing values in the dataset.")
    potential_metrics: list[str] = Field(default_factory=list, description="Suggested metric columns.")
    potential_dimensions: list[str] = Field(default_factory=list, description="Suggested dimension columns.")
    suitable_tools: list[str] = Field(default_factory=list, description="Tools appropriate for this dataset.")

    @field_validator('dataset_name')
    @classmethod
    def dataset_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('dataset_name must not be empty')
        return v

    @field_validator('row_count', 'column_count', 'missing_value_count')
    @classmethod
    def counts_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Value must not be negative')
        return v


class ClarificationRequest(BaseModel):
    """
    Returned when the pipeline cannot deterministically resolve required schema fields.
    """
    clarification_type: str = Field(
        ...,
        description="Type of clarification needed: metric, dimension, comparison_target, or date_column.",
    )
    message: str = Field(..., description="User-facing explanation of what is ambiguous.")
    options: list[str] = Field(
        default_factory=list,
        description="Valid choices the user can select from.",
    )

    @field_validator("clarification_type")
    @classmethod
    def clarification_type_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("clarification_type must not be empty")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        return v

    @field_validator("options")
    @classmethod
    def options_not_empty(cls, v: list[str]) -> list[str]:
        cleaned = [option.strip() for option in v if option.strip()]
        if not cleaned:
            raise ValueError("options must contain at least one non-empty value")
        return cleaned


class AnalysisRequest(BaseModel):
    """
    Request describing a data analysis or question for one or more datasets.
    """
    question: str = Field(..., description="Natural language question or analysis objective.")
    dataset_names: list[str] = Field(default_factory=list, description="Names of datasets to analyze.")
    requested_analysis_type: str | None = Field(None, description="Optional analysis type (if any).")
    selected_metrics: list[str] = Field(default_factory=list, description="Metrics for the analysis.")
    selected_dimensions: list[str] = Field(default_factory=list, description="Dimensions for grouping or slicing.")
    selected_comparison_direction: str | None = Field(
        None,
        description="Optional comparison direction: top, bottom, or dual.",
    )
    selected_date_column: str | None = Field(
        None,
        description="Date/time column selected for temporal filtering.",
    )

    @field_validator('question')
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('question must not be empty')
        return v


class TemporalFilterContext(BaseModel):
    """Metadata describing a temporal filter applied before analysis."""

    label: str = Field(..., description="Human-readable period label, e.g. April 2026.")
    date_column: str = Field(..., description="Date column used for temporal filtering.")
    original_row_count: int = Field(..., description="Rows in the dataset before filtering.")
    filtered_row_count: int = Field(..., description="Rows remaining after filtering.")
    date_column_inferred: bool = Field(
        ...,
        description="True when the date column was auto-selected rather than explicit.",
    )

    @field_validator("label", "date_column")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Value must not be empty")
        return v

    @field_validator("original_row_count", "filtered_row_count")
    @classmethod
    def counts_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value must not be negative")
        return v


class SnapshotContributor(BaseModel):
    """Highest or lowest group contributing to a snapshot metric."""

    dimension_name: str = Field(..., description="Dimension column used for grouping.")
    entity_name: str = Field(..., description="Dimension value for the contributor.")
    value: float | int = Field(..., description="Aggregated metric value for the entity.")

    @field_validator("dimension_name", "entity_name")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Value must not be empty")
        return v


class SnapshotContext(BaseModel):
    """Metadata describing snapshot analytical mode activation."""

    activated: bool = Field(..., description="True when snapshot mode replaced trend analysis.")
    reason: str = Field(..., description="Why snapshot mode was activated.")
    period_label: str = Field(..., description="Human-readable label for the scoped period.")
    bucket_count: int = Field(..., description="Distinct temporal buckets in the scoped dataset.")

    @field_validator("reason", "period_label")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Value must not be empty")
        return v

    @field_validator("bucket_count")
    @classmethod
    def bucket_count_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("bucket_count must be at least 1 when snapshot mode is active")
        return v


class EvidenceItem(BaseModel):
    """
    Represents a discrete piece of evidence supporting a finding.
    """
    description: str = Field(..., description="Explanation for this evidence item.")
    dataset_name: str | None = Field(None, description="Associated dataset, if relevant.")
    metric_name: str | None = Field(None, description="Metric's name, if relevant.")
    metric_value: float | int | str | None = Field(None, description="Value of the metric, if available.")
    supporting_context: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, description="Additional metadata or context."
    )

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('description must not be empty')
        return v

    @field_validator('dataset_name', 'metric_name')
    @classmethod
    def optional_str_nonempty_if_present(cls, v: str | None) -> str | None:
        if v is not None:
            v2 = v.strip()
            if not v2:
                raise ValueError('Optional string fields must not be empty if provided')
            return v2
        return v


class ToolResult(BaseModel):
    """
    Captures the outcome of running a tooling operation on a dataset or analysis.
    """
    tool_name: str = Field(..., description="Name of the executed analysis tool.")
    success: bool = Field(..., description="Whether tool execution succeeded.")
    summary: str = Field(..., description="Summary description of the result.")
    evidence_items: list[EvidenceItem] = Field(default_factory=list, description="Supporting evidence collected.")
    warnings: list[str] = Field(default_factory=list, description="Warnings emitted during execution, if any.")

    @field_validator('tool_name')
    @classmethod
    def tool_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('tool_name must not be empty')
        return v

    @field_validator('summary')
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('summary must not be empty')
        return v


class Finding(BaseModel):
    """
    Represents an insight, anomaly, or noteworthy analysis result.
    """
    title: str = Field(..., description="Short title for the finding.")
    description: str = Field(..., description="Detailed explanation of the finding.")
    severity: str = Field(..., description="Severity: INFO, LOW, MEDIUM, HIGH.")
    confidence: str = Field(..., description="Confidence: LOW, MEDIUM, HIGH.")
    evidence: list[EvidenceItem] = Field(default_factory=list, description="Evidence supporting this finding.")
    recommended_action: str | None = Field(None, description="Follow-up or actionable recommendation, if any.")
    finding_id: str | None = Field(
        None,
        description="Stable identifier for executive reasoning references.",
    )
    finding_type: str | None = Field(
        None,
        description="Provenance type: anomaly, variance, trend, snapshot, or failure.",
    )
    source_tool: str | None = Field(
        None,
        description="Originating analytical tool name.",
    )

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('title must not be empty')
        return v

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('description must not be empty')
        return v

    @field_validator('severity')
    @classmethod
    def severity_check(cls, v: str) -> str:
        allowed = {"INFO", "LOW", "MEDIUM", "HIGH"}
        v_up = v.strip().upper()
        if v_up not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v_up

    @field_validator('confidence')
    @classmethod
    def confidence_check(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH"}
        v_up = v.strip().upper()
        if v_up not in allowed:
            raise ValueError(f"confidence must be one of {allowed}")
        return v_up

    @field_validator('recommended_action')
    @classmethod
    def recommended_action_nonempty_if_present(cls, v: str | None) -> str | None:
        if v is not None:
            v2 = v.strip()
            if not v2:
                raise ValueError('recommended_action must not be empty if provided')
            return v2
        return v

    @field_validator('finding_id', 'source_tool')
    @classmethod
    def optional_provenance_str_nonempty_if_present(cls, v: str | None) -> str | None:
        if v is not None:
            v2 = v.strip()
            if not v2:
                raise ValueError('Value must not be empty if provided')
            return v2
        return v

    @field_validator('finding_type')
    @classmethod
    def finding_type_check(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"anomaly", "variance", "trend", "snapshot", "failure"}
        v_lower = v.strip().lower()
        if v_lower not in allowed:
            raise ValueError(f"finding_type must be one of {allowed}")
        return v_lower

class PipelineAnalysisResult(BaseModel):
    """Outcome of a completed pipeline run with optional temporal metadata."""

    findings: list[Finding] = Field(default_factory=list)
    temporal_filter: TemporalFilterContext | None = Field(
        None,
        description="Temporal filter metadata when explicit period filtering was applied.",
    )
    snapshot_context: SnapshotContext | None = Field(
        None,
        description="Snapshot mode metadata when single-bucket trend analysis was substituted.",
    )


class ExecutiveReport(BaseModel):
    """
    Executive-ready operational intelligence report summarising
    findings, priorities, and recommended actions.
    """
    executive_summary: str = Field(..., description="Concise executive summary of the overall findings.")
    high_priority_findings: list[Finding] = Field(default_factory=list, description="Findings with HIGH severity.")
    medium_priority_findings: list[Finding] = Field(default_factory=list, description="Findings with MEDIUM severity.")
    low_priority_findings: list[Finding] = Field(default_factory=list, description="Findings with LOW or INFO severity.")
    recommended_next_steps: list[str] = Field(default_factory=list, description="Recommended follow-up steps.")
    suggested_follow_up_investigations: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up investigations derived from findings.",
    )
    operational_assessment: "OperationalAssessment | None" = Field(
        None,
        description="Overall operational assessment from executive reasoning.",
    )
    executive_conclusions: list["ExecutiveConclusion"] = Field(
        default_factory=list,
        description="Structured executive conclusions by theme.",
    )
    priority_actions: list["PriorityAction"] = Field(
        default_factory=list,
        description="Ranked priority actions from executive reasoning.",
    )
    executive_themes: list["ExecutiveTheme"] = Field(
        default_factory=list,
        description="Executive themes grouped from findings.",
    )

    @field_validator('executive_summary')
    @classmethod
    def executive_summary_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('executive_summary must not be empty')
        return v
   