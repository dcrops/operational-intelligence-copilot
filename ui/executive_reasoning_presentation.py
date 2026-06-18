"""Pure formatting helpers for executive reasoning sections in the UI."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.operational_intelligence.executive_conclusions import ExecutiveConclusion
from src.operational_intelligence.executive_reasoning import ExecutiveTheme
from src.operational_intelligence.models import ExecutiveReport, Finding
from src.operational_intelligence.operational_assessment import (
    ASSESSMENT_CRITICAL,
    ASSESSMENT_HEALTHY,
    ASSESSMENT_NEEDS_ATTENTION,
    ASSESSMENT_REQUIRES_MONITORING,
    OperationalAssessment,
)
from src.operational_intelligence.priority_actions import PriorityAction
from ui.metric_presentation import humanise_metric_name, humanise_user_facing_text

ANALYSIS_OVERVIEW_HEADING = "Analysis Overview"
ANALYTICAL_FINDINGS_HEADING = "Analytical Findings"
EXECUTIVE_REASONING_HEADING = "Executive Reasoning"
EVIDENCE_CONSIDERED_HEADING = "Evidence Considered"
DEFAULT_INVESTIGATION_LIMIT = 3
ADDITIONAL_INVESTIGATIONS_EXPANDER_LABEL = "Show additional investigations"

ASSESSMENT_LEVEL_INDICATORS = {
    ASSESSMENT_HEALTHY: "🟢",
    ASSESSMENT_REQUIRES_MONITORING: "🟡",
    ASSESSMENT_NEEDS_ATTENTION: "🟠",
    ASSESSMENT_CRITICAL: "🔴",
}

_TOOL_LABELS = {
    "anomaly_detection": "Anomaly detection",
    "variance_analysis": "Variance analysis",
    "trend_analysis": "Trend analysis",
    "risk_assessment": "Risk assessment",
    "snapshot_analysis": "Snapshot analysis",
}

_OPERATIONAL_RISK_SUMMARY = {
    ASSESSMENT_HEALTHY: "Low operational risk",
    ASSESSMENT_REQUIRES_MONITORING: "Low operational risk",
    ASSESSMENT_NEEDS_ATTENTION: "Moderate operational risk",
    ASSESSMENT_CRITICAL: "High operational risk",
}

_PRIORITY_RATIONALE_PATTERN = re.compile(
    r"^Based on (?P<severity>[A-Z]+) severity (?P<finding_type>[a-z]+) finding\(s\) linked to .+\.$",
    re.IGNORECASE,
)

_PRIORITY_ACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"^Review snapshot performance for (?P<metric>.+?) against baseline\.$",
            re.IGNORECASE,
        ),
        "Review {metric} against the historical baseline.",
    ),
    (
        re.compile(
            r"^Monitor trend movement linked to (?P<metric>.+?)\.$",
            re.IGNORECASE,
        ),
        "Review trend movement in {metric}.",
    ),
    (
        re.compile(
            r"^Review group differences linked to (?P<metric>.+?)\.$",
            re.IGNORECASE,
        ),
        "Review group differences in {metric}.",
    ),
    (
        re.compile(
            r"^Investigate anomalous records linked to (?P<metric>.+?)\.$",
            re.IGNORECASE,
        ),
        "Investigate anomalous records in {metric}.",
    ),
    (
        re.compile(
            r"^Review analysis failure linked to (?P<metric>.+?)\.$",
            re.IGNORECASE,
        ),
        "Review the analysis failure linked to {metric}.",
    ),
)

_SEVERITY_FALLBACK_RATIONALE = {
    "HIGH": "High-severity findings should be reviewed before operational decisions are made.",
    "MEDIUM": "Medium-severity findings warrant closer monitoring and follow-up review.",
    "LOW": "Lower-severity findings should continue to be monitored for emerging patterns.",
    "INFO": "Informational findings provide context and should remain under routine monitoring.",
}

_PRIORITY_RATIONALE_TEMPLATES: dict[tuple[str, str], str] = {
    ("HIGH", "anomaly"): (
        "High-severity anomalies should be investigated before operational decisions are made."
    ),
    ("HIGH", "variance"): (
        "High-severity differences between groups should be reviewed before operational "
        "decisions are made."
    ),
    ("HIGH", "trend"): (
        "High-severity trend movement should be monitored before operational decisions are made."
    ),
    ("HIGH", "snapshot"): (
        "High-severity snapshot results should be reviewed before operational decisions are made."
    ),
    ("HIGH", "failure"): (
        "High-severity analysis failures should be resolved before operational decisions are made."
    ),
    ("MEDIUM", "anomaly"): (
        "Medium-severity anomalies warrant closer monitoring and follow-up review."
    ),
    ("MEDIUM", "variance"): (
        "Medium-severity group differences warrant closer monitoring and follow-up review."
    ),
    ("MEDIUM", "trend"): (
        "Medium-severity trend movement warrants closer monitoring and follow-up review."
    ),
    ("MEDIUM", "snapshot"): (
        "Medium-severity snapshot results warrant closer monitoring and follow-up review."
    ),
    ("MEDIUM", "failure"): (
        "Medium-severity analysis failures warrant closer monitoring and follow-up review."
    ),
    ("LOW", "anomaly"): (
        "Lower-severity anomalies should continue to be monitored for emerging patterns."
    ),
    ("LOW", "variance"): (
        "Lower-severity group differences should continue to be monitored for emerging patterns."
    ),
    ("LOW", "trend"): (
        "Lower-severity trend movement should continue to be monitored for emerging patterns."
    ),
    ("LOW", "snapshot"): (
        "Lower-severity snapshot findings should continue to be monitored for emerging patterns."
    ),
    ("LOW", "failure"): (
        "Lower-severity analysis failures should continue to be monitored for emerging patterns."
    ),
    ("INFO", "anomaly"): (
        "Informational anomaly signals provide context and should remain under routine monitoring."
    ),
    ("INFO", "variance"): (
        "Informational variance signals provide context and should remain under routine monitoring."
    ),
    ("INFO", "trend"): (
        "Informational trend signals provide context and should remain under routine monitoring."
    ),
    ("INFO", "snapshot"): (
        "Informational snapshot signals provide context and should remain under routine monitoring."
    ),
    ("INFO", "failure"): (
        "Informational analysis failures provide context and should remain under routine monitoring."
    ),
}


@dataclass(frozen=True)
class OperationalAssessmentPresentation:
    level: str
    level_display: str
    explanation: str


@dataclass(frozen=True)
class AnalysisOverviewPresentation:
    bullets: list[str]


@dataclass(frozen=True)
class ExecutiveConclusionPresentation:
    title: str
    insight: str
    evidence_heading: str
    evidence_bullets: list[str]


@dataclass(frozen=True)
class PriorityActionPresentation:
    header: str
    action_text: str
    reason_label: str
    reason_text: str


@dataclass(frozen=True)
class FollowUpInvestigationPresentation:
    visible: list[str]
    additional: list[str]
    expander_label: str


def should_show_executive_reasoning(report: ExecutiveReport) -> bool:
    return (
        should_show_operational_assessment(report)
        or should_show_executive_conclusions(report)
        or should_show_priority_actions(report)
    )


def should_show_operational_assessment(report: ExecutiveReport) -> bool:
    return report.operational_assessment is not None


def should_show_executive_conclusions(report: ExecutiveReport) -> bool:
    return bool(report.executive_conclusions)


def should_show_priority_actions(report: ExecutiveReport) -> bool:
    return bool(report.priority_actions)


def should_show_recommended_actions(report: ExecutiveReport) -> bool:
    """Hide when priority actions already present the same content."""
    if report.priority_actions:
        return False
    return bool(report.recommended_next_steps)


def humanise_theme_label(label: str) -> str:
    return humanise_metric_name(label)


def theme_label_from_conclusion(conclusion: ExecutiveConclusion) -> str:
    if ": " in conclusion.headline:
        return conclusion.headline.split(": ", 1)[1]
    return conclusion.headline


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


def _theme_for_conclusion(
    conclusion: ExecutiveConclusion,
    report: ExecutiveReport,
) -> ExecutiveTheme | None:
    for theme in report.executive_themes:
        if theme.theme_id == conclusion.primary_theme:
            return theme
    return None


def _strip_bullet_prefix(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("• "):
            cleaned = cleaned[2:].strip()
        if cleaned:
            lines.append(cleaned)
    return "\n\n".join(lines)


def format_assessment_level_display(level: str) -> str:
    indicator = ASSESSMENT_LEVEL_INDICATORS.get(level, "")
    if indicator:
        return f"{indicator} {level}"
    return level


def _humanise_tool_name(tool_name: str) -> str:
    if tool_name in _TOOL_LABELS:
        return _TOOL_LABELS[tool_name]
    return tool_name.replace("_", " ").capitalize()


def format_analysis_overview(
    *,
    findings: list[Finding],
    routes: list[str],
    report: ExecutiveReport,
) -> AnalysisOverviewPresentation:
    findings_count = len(findings)
    finding_word = "finding" if findings_count == 1 else "findings"
    bullets = [f"{findings_count} analytical {finding_word}"]

    seen_tools: set[str] = set()
    for route in routes:
        label = _humanise_tool_name(route)
        if label in seen_tools:
            continue
        seen_tools.add(label)
        bullets.append(f"{label} executed")

    if report.operational_assessment is not None:
        risk_summary = _OPERATIONAL_RISK_SUMMARY.get(
            report.operational_assessment.assessment_level,
            "Operational risk assessed",
        )
        bullets.append(risk_summary)

    return AnalysisOverviewPresentation(bullets=bullets)


def format_operational_assessment(
    assessment: OperationalAssessment,
) -> OperationalAssessmentPresentation:
    return OperationalAssessmentPresentation(
        level=assessment.assessment_level,
        level_display=format_assessment_level_display(assessment.assessment_level),
        explanation=_strip_bullet_prefix(assessment.rationale),
    )


def summarize_finding_evidence(finding: Finding) -> str:
    finding_type = _resolve_finding_type(finding)
    description = finding.description.lower()

    if finding_type == "trend":
        if "volatile" in description:
            return "Trend analysis detected increased volatility."
        if "increas" in description:
            return "Trend analysis detected upward movement over time."
        if "decreas" in description:
            return "Trend analysis detected downward movement over time."
        if "stable" in description:
            return "Trend analysis detected relatively stable movement."
        return "Trend analysis detected movement over time."

    if finding_type == "variance":
        return "Variance analysis identified material differences between groups."

    if finding_type == "snapshot":
        if "below" in description:
            return "Snapshot analysis found performance below baseline."
        if "above" in description:
            return "Snapshot analysis found performance above baseline."
        return "Snapshot analysis found performance relative to baseline."

    if finding_type == "anomaly":
        return "Anomaly detection identified abnormal operational records."

    if finding_type == "failure":
        return "Analysis failure was recorded for this theme."

    return "Supporting analytical evidence was recorded for this theme."


def synthesize_conclusion_insight(
    title: str,
    findings: list[Finding],
    assessment_level: str,
) -> str:
    if not findings:
        if assessment_level == "Healthy":
            return f"{title} appears broadly stable based on available evidence."
        return f"{title} should continue to be monitored."

    finding_types = {_resolve_finding_type(finding) for finding in findings}
    severities = {(finding.severity or "INFO").upper() for finding in findings}
    descriptions = " ".join(finding.description.lower() for finding in findings)

    if "snapshot" in finding_types:
        if "below" in descriptions:
            return (
                f"{title} remains slightly below its historical baseline "
                "and should continue to be monitored."
            )
        if "above" in descriptions:
            return (
                f"{title} remains above its historical baseline "
                "and should continue to be monitored."
            )
        return (
            f"{title} differs from its historical baseline "
            "and should continue to be monitored."
        )

    if "HIGH" in severities:
        if "anomaly" in finding_types:
            return (
                f"{title} shows high-severity anomalies that require immediate operational review."
            )
        if "variance" in finding_types:
            return (
                f"{title} shows high-severity group differences that require immediate "
                "operational review."
            )
        return f"{title} shows high-severity signals that require immediate operational review."

    if "MEDIUM" in severities:
        if "variance" in finding_types:
            return (
                f"{title} shows material differences across groups that warrant executive attention."
            )
        if "trend" in finding_types:
            return f"{title} shows emerging trend movement that warrants executive attention."
        return f"{title} shows medium-severity signals that warrant executive attention."

    if "volatile" in descriptions or any(
        _resolve_finding_type(finding) == "trend" and "volatile" in finding.description.lower()
        for finding in findings
    ):
        return f"{title} shows increased volatility and should continue to be monitored."

    if "variance" in finding_types:
        return f"{title} shows group differences that should continue to be monitored."

    if "anomaly" in finding_types:
        return f"{title} shows anomaly signals that should continue to be monitored."

    return f"{title} should continue to be monitored."


def _evidence_bullets_for_theme(theme: ExecutiveTheme | None) -> list[str]:
    if theme is None or not theme.findings:
        return []

    bullets: list[str] = []
    seen: set[str] = set()
    for finding in theme.findings:
        summary = summarize_finding_evidence(finding)
        if summary in seen:
            continue
        seen.add(summary)
        bullets.append(summary)
    return bullets


def format_executive_conclusion(
    conclusion: ExecutiveConclusion,
    report: ExecutiveReport,
) -> ExecutiveConclusionPresentation:
    title = humanise_theme_label(theme_label_from_conclusion(conclusion))
    theme = _theme_for_conclusion(conclusion, report)
    findings = list(theme.findings) if theme is not None else []

    return ExecutiveConclusionPresentation(
        title=title,
        insight=synthesize_conclusion_insight(
            title,
            findings,
            conclusion.assessment_level,
        ),
        evidence_heading=EVIDENCE_CONSIDERED_HEADING,
        evidence_bullets=_evidence_bullets_for_theme(theme),
    )


def humanise_priority_rationale(rationale: str) -> str:
    match = _PRIORITY_RATIONALE_PATTERN.match(rationale.strip())
    if match is None:
        return humanise_user_facing_text(rationale)

    severity = match.group("severity").upper()
    finding_type = match.group("finding_type").lower()
    template = _PRIORITY_RATIONALE_TEMPLATES.get((severity, finding_type))
    if template is not None:
        return template
    return _SEVERITY_FALLBACK_RATIONALE.get(severity, humanise_user_facing_text(rationale))


def humanise_priority_action_text(action: str) -> str:
    text = action.strip()
    for pattern, template in _PRIORITY_ACTION_PATTERNS:
        match = pattern.match(text)
        if match is not None:
            metric = humanise_metric_name(match.group("metric"))
            return template.format(metric=metric)
    return humanise_user_facing_text(text)


def format_priority_action(action: PriorityAction) -> PriorityActionPresentation:
    return PriorityActionPresentation(
        header=f"Priority {action.rank} • {action.urgency}",
        action_text=humanise_priority_action_text(action.action),
        reason_label="Reason",
        reason_text=humanise_priority_rationale(action.rationale),
    )


def split_follow_up_investigations(
    investigations: list[str],
    *,
    limit: int = DEFAULT_INVESTIGATION_LIMIT,
) -> FollowUpInvestigationPresentation:
    return FollowUpInvestigationPresentation(
        visible=list(investigations[:limit]),
        additional=list(investigations[limit:]),
        expander_label=ADDITIONAL_INVESTIGATIONS_EXPANDER_LABEL,
    )
