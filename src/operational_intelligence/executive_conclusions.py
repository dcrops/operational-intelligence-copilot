"""Structured executive conclusions derived from themes and assessment."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.operational_assessment import (
    ALLOWED_ASSESSMENT_LEVELS,
    OperationalAssessment,
)
from src.operational_intelligence.models import Finding


class ExecutiveConclusion(BaseModel):
    """Structured executive reasoning for a single theme."""

    conclusion_id: str = Field(..., description="Stable identifier for the conclusion.")
    headline: str = Field(..., description="Short deterministic summary headline.")
    assessment_level: str = Field(
        ...,
        description="Operational assessment level applied to this conclusion.",
    )
    primary_theme: str = Field(..., description="Primary theme identifier.")
    supporting_finding_ids: list[str] = Field(default_factory=list)
    supporting_theme_ids: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)

    @field_validator(
        "conclusion_id",
        "headline",
        "primary_theme",
    )
    @classmethod
    def non_empty_str(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("assessment_level")
    @classmethod
    def assessment_level_must_be_allowed(cls, value: str) -> str:
        value = value.strip()
        if value not in ALLOWED_ASSESSMENT_LEVELS:
            raise ValueError(f"assessment_level must be one of {sorted(ALLOWED_ASSESSMENT_LEVELS)}")
        return value


def _headline_for_theme(theme: ExecutiveTheme, assessment: OperationalAssessment) -> str:
    return f"{assessment.assessment_level}: {theme.theme_label}"


def _evidence_summary_for_finding(finding: Finding) -> str:
    description = finding.description.strip()
    if description:
        return description
    if finding.title.strip():
        return finding.title.strip()
    return "Finding recorded without descriptive summary."


def _evidence_summary_for_theme(theme: ExecutiveTheme) -> list[str]:
    summaries: list[str] = []
    seen: set[str] = set()
    for finding in theme.findings:
        summary = _evidence_summary_for_finding(finding)
        if summary in seen:
            continue
        seen.add(summary)
        summaries.append(summary)
    return summaries


class ExecutiveConclusionEngine:
    """Build structured executive conclusions from themes and assessment."""

    def build(
        self,
        themes: list[ExecutiveTheme],
        assessment: OperationalAssessment,
    ) -> list[ExecutiveConclusion]:
        if not isinstance(themes, list):
            raise ValueError("themes must be a list")
        if not isinstance(assessment, OperationalAssessment):
            raise ValueError("assessment must be an OperationalAssessment")

        conclusions: list[ExecutiveConclusion] = []
        for index, theme in enumerate(themes):
            conclusions.append(
                ExecutiveConclusion(
                    conclusion_id=f"conclusion-{index}",
                    headline=_headline_for_theme(theme, assessment),
                    assessment_level=assessment.assessment_level,
                    primary_theme=theme.theme_id,
                    supporting_finding_ids=list(theme.finding_ids),
                    supporting_theme_ids=[theme.theme_id],
                    evidence_summary=_evidence_summary_for_theme(theme),
                )
            )
        return conclusions
