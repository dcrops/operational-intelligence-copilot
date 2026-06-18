"""Deterministic operational assessment over executive themes."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import Finding

ASSESSMENT_HEALTHY = "Healthy"
ASSESSMENT_REQUIRES_MONITORING = "Requires Monitoring"
ASSESSMENT_NEEDS_ATTENTION = "Needs Attention"
ASSESSMENT_CRITICAL = "Critical"

ALLOWED_ASSESSMENT_LEVELS = {
    ASSESSMENT_HEALTHY,
    ASSESSMENT_REQUIRES_MONITORING,
    ASSESSMENT_NEEDS_ATTENTION,
    ASSESSMENT_CRITICAL,
}

MONITORING_SEVERITIES = {"LOW", "INFO"}


class OperationalAssessment(BaseModel):
    """Overall operational state derived from grouped findings."""

    assessment_level: str = Field(..., description="Overall operational assessment level.")
    rationale: str = Field(..., description="Deterministic explanation for the assessment.")
    supporting_finding_ids: list[str] = Field(default_factory=list)
    supporting_theme_ids: list[str] = Field(default_factory=list)

    @field_validator("assessment_level")
    @classmethod
    def assessment_level_must_be_allowed(cls, value: str) -> str:
        value = value.strip()
        if value not in ALLOWED_ASSESSMENT_LEVELS:
            raise ValueError(f"assessment_level must be one of {sorted(ALLOWED_ASSESSMENT_LEVELS)}")
        return value

    @field_validator("rationale")
    @classmethod
    def rationale_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value


class ThemeFindingEntry:
    __slots__ = ("theme_id", "finding_id", "finding")

    def __init__(self, theme_id: str, finding_id: str, finding: Finding) -> None:
        self.theme_id = theme_id
        self.finding_id = finding_id
        self.finding = finding


def _collect_theme_findings(themes: list[ExecutiveTheme]) -> list[ThemeFindingEntry]:
    entries: list[ThemeFindingEntry] = []
    for theme in themes:
        for finding_id, finding in zip(theme.finding_ids, theme.findings):
            entries.append(ThemeFindingEntry(theme.theme_id, finding_id, finding))
    return entries


def _normalized_severity(finding: Finding) -> str:
    return (finding.severity or "INFO").strip().upper()


def _supporting_from_entries(
    entries: list[ThemeFindingEntry],
) -> tuple[list[str], list[str]]:
    finding_ids = [entry.finding_id for entry in entries]
    theme_ids: list[str] = []
    seen_themes: set[str] = set()
    for entry in entries:
        if entry.theme_id not in seen_themes:
            theme_ids.append(entry.theme_id)
            seen_themes.add(entry.theme_id)
    return finding_ids, theme_ids


def _bullet(lines: list[str]) -> str:
    return "\n".join(f"• {line}" for line in lines)


def _high_severity_rationale(entries: list[ThemeFindingEntry]) -> list[str]:
    high_types = sorted(
        {
            entry.finding.finding_type
            for entry in entries
            if entry.finding.finding_type
        }
    )
    if len(high_types) == 1:
        return [f"High severity {high_types[0]} findings detected."]
    return ["High severity findings detected."]


class OperationalAssessmentEngine:
    """Classify overall operational state from executive themes."""

    def assess(self, themes: list[ExecutiveTheme]) -> OperationalAssessment:
        if not isinstance(themes, list):
            raise ValueError("themes must be a list")

        entries = _collect_theme_findings(themes)
        if not entries:
            return OperationalAssessment(
                assessment_level=ASSESSMENT_HEALTHY,
                rationale=_bullet(["No findings were identified."]),
                supporting_finding_ids=[],
                supporting_theme_ids=[],
            )

        high_entries = [
            entry for entry in entries if _normalized_severity(entry.finding) == "HIGH"
        ]
        if high_entries:
            finding_ids, theme_ids = _supporting_from_entries(high_entries)
            return OperationalAssessment(
                assessment_level=ASSESSMENT_CRITICAL,
                rationale=_bullet(_high_severity_rationale(high_entries)),
                supporting_finding_ids=finding_ids,
                supporting_theme_ids=theme_ids,
            )

        medium_entries = [
            entry for entry in entries if _normalized_severity(entry.finding) == "MEDIUM"
        ]
        if medium_entries:
            finding_ids, theme_ids = _supporting_from_entries(medium_entries)
            return OperationalAssessment(
                assessment_level=ASSESSMENT_NEEDS_ATTENTION,
                rationale=_bullet(["Medium severity findings detected."]),
                supporting_finding_ids=finding_ids,
                supporting_theme_ids=theme_ids,
            )

        low_entries = [
            entry
            for entry in entries
            if _normalized_severity(entry.finding) in MONITORING_SEVERITIES
        ]
        low_theme_ids = sorted({entry.theme_id for entry in low_entries})
        if len(low_theme_ids) >= 2:
            finding_ids, theme_ids = _supporting_from_entries(low_entries)
            return OperationalAssessment(
                assessment_level=ASSESSMENT_NEEDS_ATTENTION,
                rationale=_bullet(["Multiple operational themes require attention."]),
                supporting_finding_ids=finding_ids,
                supporting_theme_ids=theme_ids,
            )

        finding_ids, theme_ids = _supporting_from_entries(low_entries)
        return OperationalAssessment(
            assessment_level=ASSESSMENT_REQUIRES_MONITORING,
            rationale=_bullet(["Only low-severity findings were identified."]),
            supporting_finding_ids=finding_ids,
            supporting_theme_ids=theme_ids,
        )
