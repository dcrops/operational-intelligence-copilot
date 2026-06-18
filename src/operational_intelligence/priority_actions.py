"""Deterministic priority actions derived from themes, assessment, and conclusions."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from src.operational_intelligence.executive_conclusions import ExecutiveConclusion
from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import Finding
from src.operational_intelligence.operational_assessment import (
    ASSESSMENT_CRITICAL,
    ASSESSMENT_HEALTHY,
    ASSESSMENT_NEEDS_ATTENTION,
    ASSESSMENT_REQUIRES_MONITORING,
    OperationalAssessment,
)

ALLOWED_URGENCY_LEVELS = {"Immediate", "Soon", "Monitor"}

URGENCY_BY_ASSESSMENT = {
    ASSESSMENT_CRITICAL: "Immediate",
    ASSESSMENT_NEEDS_ATTENTION: "Soon",
    ASSESSMENT_REQUIRES_MONITORING: "Monitor",
    ASSESSMENT_HEALTHY: "Monitor",
}

SEVERITY_RANK = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
    "INFO": 3,
}

FINDING_TYPE_ORDER = ("anomaly", "variance", "snapshot", "trend", "failure")

ACTION_TEXT_BY_FINDING_TYPE = {
    "anomaly": "Investigate anomalous records linked to {theme_label}.",
    "variance": "Review group differences linked to {theme_label}.",
    "trend": "Monitor trend movement linked to {theme_label}.",
    "snapshot": "Review snapshot performance for {theme_label} against baseline.",
    "failure": "Review analysis failure linked to {theme_label}.",
}

_CAUSATION_BLACKLIST = (
    "caused by",
    "because of",
    "due to",
    "proves",
    "responsible for",
    "root cause",
    "driven by",
)

MAX_PRIORITY_ACTIONS = 5


class PriorityAction(BaseModel):
    """Structured, evidence-backed operational action."""

    action_id: str = Field(..., description="Stable identifier for the action.")
    rank: int = Field(..., description="Deterministic priority rank starting at 1.")
    urgency: str = Field(..., description="Immediate, Soon, or Monitor.")
    action: str = Field(..., description="Concise evidence-backed action text.")
    rationale: str = Field(..., description="Deterministic reason for the action.")
    linked_finding_ids: list[str] = Field(default_factory=list)
    linked_theme_ids: list[str] = Field(default_factory=list)
    linked_conclusion_ids: list[str] = Field(default_factory=list)

    @field_validator("action_id", "action", "rationale")
    @classmethod
    def non_empty_str(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("urgency")
    @classmethod
    def urgency_must_be_allowed(cls, value: str) -> str:
        value = value.strip()
        if value not in ALLOWED_URGENCY_LEVELS:
            raise ValueError(f"urgency must be one of {sorted(ALLOWED_URGENCY_LEVELS)}")
        return value

    @field_validator("rank")
    @classmethod
    def rank_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("rank must be at least 1")
        return value

    @model_validator(mode="after")
    def traceability_fields_present(self) -> PriorityAction:
        if not self.linked_finding_ids:
            raise ValueError("linked_finding_ids must contain at least one finding ID")
        if not self.linked_theme_ids:
            raise ValueError("linked_theme_ids must contain at least one theme ID")
        return self


def _normalized_severity(finding: Finding) -> str:
    return (finding.severity or "INFO").strip().upper()


def _resolve_finding_type(finding: Finding) -> str | None:
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


def _finding_type_sort_key(finding_type: str) -> int:
    if finding_type in FINDING_TYPE_ORDER:
        return FINDING_TYPE_ORDER.index(finding_type)
    return len(FINDING_TYPE_ORDER)


def _theme_max_severity_rank(theme: ExecutiveTheme) -> int:
    if not theme.findings:
        return len(SEVERITY_RANK)
    return min(
        SEVERITY_RANK.get(_normalized_severity(finding), len(SEVERITY_RANK))
        for finding in theme.findings
    )


def _primary_finding_type(theme: ExecutiveTheme) -> str:
    ranked_findings = sorted(
        theme.findings,
        key=lambda finding: (
            SEVERITY_RANK.get(_normalized_severity(finding), len(SEVERITY_RANK)),
            _finding_type_sort_key(_resolve_finding_type(finding) or ""),
        ),
    )
    for finding in ranked_findings:
        finding_type = _resolve_finding_type(finding)
        if finding_type is not None:
            return finding_type
    return "trend"


def _severity_label(rank: int) -> str:
    for label, value in SEVERITY_RANK.items():
        if value == rank:
            return label
    return "INFO"


def _action_text(finding_type: str, theme_label: str) -> str:
    template = ACTION_TEXT_BY_FINDING_TYPE.get(
        finding_type,
        "Review operational signals linked to {theme_label}.",
    )
    return template.format(theme_label=theme_label)


def _rationale_for_theme(theme: ExecutiveTheme, finding_type: str) -> str:
    severity_rank = _theme_max_severity_rank(theme)
    severity_label = _severity_label(severity_rank)
    return (
        f"Based on {severity_label} severity {finding_type} finding(s) "
        f"linked to {theme.theme_label}."
    )


def _validate_action_text(text: str) -> str:
    lowered = text.lower()
    for phrase in _CAUSATION_BLACKLIST:
        if phrase in lowered:
            raise ValueError(
                f"Action contains disallowed causation phrase {phrase!r}: {text!r}"
            )
    return text


class PriorityActionEngine:
    """Build ranked priority actions from executive reasoning artifacts."""

    def build(
        self,
        themes: list[ExecutiveTheme],
        assessment: OperationalAssessment,
        conclusions: list[ExecutiveConclusion],
    ) -> list[PriorityAction]:
        if not isinstance(themes, list):
            raise ValueError("themes must be a list")
        if not isinstance(assessment, OperationalAssessment):
            raise ValueError("assessment must be an OperationalAssessment")
        if not isinstance(conclusions, list):
            raise ValueError("conclusions must be a list")

        if assessment.assessment_level == ASSESSMENT_HEALTHY:
            if not any(theme.findings for theme in themes):
                return []

        urgency = URGENCY_BY_ASSESSMENT.get(assessment.assessment_level)
        if urgency is None:
            return []

        conclusion_by_theme = {
            conclusion.primary_theme: conclusion for conclusion in conclusions
        }

        candidates: list[tuple[int, int, ExecutiveTheme, str | None]] = []
        for theme_index, theme in enumerate(themes):
            if not theme.findings:
                continue
            conclusion = conclusion_by_theme.get(theme.theme_id)
            candidates.append(
                (
                    _theme_max_severity_rank(theme),
                    theme_index,
                    theme,
                    conclusion.conclusion_id if conclusion is not None else None,
                )
            )

        candidates.sort(key=lambda item: (item[0], item[1]))
        selected = candidates[:MAX_PRIORITY_ACTIONS]

        actions: list[PriorityAction] = []
        for rank, (_, _, theme, conclusion_id) in enumerate(selected, start=1):
            finding_type = _primary_finding_type(theme)
            action_text = _validate_action_text(
                _action_text(finding_type, theme.theme_label)
            )
            rationale = _validate_action_text(_rationale_for_theme(theme, finding_type))
            linked_conclusion_ids = [conclusion_id] if conclusion_id else []

            actions.append(
                PriorityAction(
                    action_id=f"action-{rank - 1}",
                    rank=rank,
                    urgency=urgency,
                    action=action_text,
                    rationale=rationale,
                    linked_finding_ids=list(theme.finding_ids),
                    linked_theme_ids=[theme.theme_id],
                    linked_conclusion_ids=linked_conclusion_ids,
                )
            )

        return actions
