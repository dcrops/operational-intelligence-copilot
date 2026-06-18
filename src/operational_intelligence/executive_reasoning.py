"""Deterministic executive reasoning over analytical findings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from src.operational_intelligence.models import EvidenceItem, Finding

if TYPE_CHECKING:
    from src.operational_intelligence.executive_conclusions import ExecutiveConclusion
    from src.operational_intelligence.operational_assessment import OperationalAssessment
    from src.operational_intelligence.priority_actions import PriorityAction

FINDING_TYPE_ORDER = ("anomaly", "variance", "trend", "snapshot", "failure")


class ExecutiveTheme(BaseModel):
    """A deterministic grouping of related findings for executive reasoning."""

    theme_id: str = Field(..., description="Stable deterministic theme identifier.")
    theme_label: str = Field(
        ...,
        description="Raw grouping label such as a metric column name or finding_type.",
    )
    finding_ids: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)

    @field_validator("theme_id", "theme_label")
    @classmethod
    def non_empty_str(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @model_validator(mode="after")
    def finding_ids_match_findings(self) -> ExecutiveTheme:
        if len(self.finding_ids) != len(self.findings):
            raise ValueError("finding_ids and findings must have the same length")
        return self


class ExecutiveReasoningResult(BaseModel):
    """Orchestrated output of the executive reasoning stack."""

    themes: list[ExecutiveTheme] = Field(default_factory=list)
    operational_assessment: OperationalAssessment
    conclusions: list[ExecutiveConclusion] = Field(default_factory=list)
    priority_actions: list[PriorityAction] = Field(default_factory=list)


def _resolve_metric(finding: Finding) -> str | None:
    """Return a single resolved metric name from evidence, or None if ambiguous."""
    metrics: list[str] = []
    seen: set[str] = set()

    for item in finding.evidence:
        if not isinstance(item, EvidenceItem):
            continue
        metric_name = item.metric_name
        if metric_name is None:
            continue
        metric_name = metric_name.strip()
        if not metric_name or metric_name in seen:
            continue
        seen.add(metric_name)
        metrics.append(metric_name)

    if len(metrics) == 1:
        return metrics[0]
    return None


def _resolve_finding_type(finding: Finding) -> str | None:
    """Return finding_type from provenance or conservative title fallback."""
    if finding.finding_type:
        return finding.finding_type

    title = finding.title.lower()
    if "anomaly" in title:
        return "anomaly"
    if "variance" in title:
        return "variance"
    if "snapshot" in title:
        return "snapshot"
    if "trend" in title:
        return "trend"
    if "failed" in title or "tool '" in title:
        return "failure"
    return None


def _finding_identifier(finding: Finding, input_index: int) -> str:
    if finding.finding_id:
        return finding.finding_id
    return f"standalone-{input_index}"


class ExecutiveReasoningEngine:
    """Group findings into executive themes using deterministic rules."""

    def group_findings(self, findings: list[Finding]) -> list[ExecutiveTheme]:
        if not isinstance(findings, list):
            raise ValueError("findings must be a list")

        if not findings:
            return []

        metric_groups: dict[str, list[tuple[int, Finding]]] = {}
        type_groups: dict[str, list[tuple[int, Finding]]] = {}
        standalone_groups: list[tuple[int, Finding]] = []

        for input_index, finding in enumerate(findings):
            metric = _resolve_metric(finding)
            if metric is not None:
                metric_groups.setdefault(metric, []).append((input_index, finding))
                continue

            finding_type = _resolve_finding_type(finding)
            if finding_type is not None:
                type_groups.setdefault(finding_type, []).append((input_index, finding))
                continue

            standalone_groups.append((input_index, finding))

        themes: list[ExecutiveTheme] = []

        for metric in sorted(metric_groups):
            grouped = metric_groups[metric]
            themes.append(
                _build_theme(
                    theme_id=f"theme-metric-{metric}",
                    theme_label=metric,
                    grouped_findings=grouped,
                )
            )

        for finding_type in sorted(type_groups, key=_finding_type_sort_key):
            grouped = type_groups[finding_type]
            themes.append(
                _build_theme(
                    theme_id=f"theme-type-{finding_type}",
                    theme_label=finding_type,
                    grouped_findings=grouped,
                )
            )

        for input_index, finding in standalone_groups:
            identifier = _finding_identifier(finding, input_index)
            themes.append(
                _build_theme(
                    theme_id=f"theme-standalone-{identifier}",
                    theme_label=identifier,
                    grouped_findings=[(input_index, finding)],
                )
            )

        return themes

    def reason(self, findings: list[Finding]) -> ExecutiveReasoningResult:
        from src.operational_intelligence.executive_conclusions import ExecutiveConclusionEngine
        from src.operational_intelligence.operational_assessment import OperationalAssessmentEngine
        from src.operational_intelligence.priority_actions import PriorityActionEngine

        if not isinstance(findings, list):
            raise ValueError("findings must be a list")

        themes = self.group_findings(findings)
        assessment = OperationalAssessmentEngine().assess(themes)
        conclusions = ExecutiveConclusionEngine().build(themes, assessment)
        priority_actions = PriorityActionEngine().build(themes, assessment, conclusions)

        return ExecutiveReasoningResult(
            themes=themes,
            operational_assessment=assessment,
            conclusions=conclusions,
            priority_actions=priority_actions,
        )


def _finding_type_sort_key(finding_type: str) -> tuple[int, str]:
    if finding_type in FINDING_TYPE_ORDER:
        return (FINDING_TYPE_ORDER.index(finding_type), finding_type)
    return (len(FINDING_TYPE_ORDER), finding_type)


def _build_theme(
    *,
    theme_id: str,
    theme_label: str,
    grouped_findings: list[tuple[int, Finding]],
) -> ExecutiveTheme:
    ordered = sorted(grouped_findings, key=lambda pair: pair[0])
    theme_findings = [finding for _, finding in ordered]
    finding_ids = [_finding_identifier(finding, input_index) for input_index, finding in ordered]

    return ExecutiveTheme(
        theme_id=theme_id,
        theme_label=theme_label,
        finding_ids=finding_ids,
        findings=theme_findings,
    )
