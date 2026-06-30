"""Translate deterministic analysis into executive business context."""

from __future__ import annotations

from src.operational_intelligence.llm.business_narrative_translation import (
    BusinessNarrativeTranslator,
)
from src.operational_intelligence.llm.executive_language import (
    collapse_multiline_text,
    extract_quoted_identifiers,
    extract_snake_case_identifiers,
    is_analytical_telemetry,
    is_implementation_title,
    split_sentences,
)
from src.operational_intelligence.llm.narrative_models import ExecutiveContext, NarrativeRequest

_DEFAULT_TRANSLATOR = BusinessNarrativeTranslator()

DEFAULT_INVESTIGATION_CATEGORIES = (
    "operational disruption",
    "staffing or capacity changes",
    "reporting or process changes",
    "seasonal or timing effects",
    "data quality or reporting inconsistency",
)

_ANALYTICAL_TITLE_PREFIXES = (
    "anomaly detection",
    "variance analysis",
    "trend analysis",
    "snapshot analysis",
    "unusual performance pattern",
    "unusual value identification",
    "attendance anomaly",
    "defect variance",
)

def _person_dimensions_for_request(
    request: NarrativeRequest,
    translator: BusinessNarrativeTranslator,
) -> tuple[str, ...]:
    return translator.extract_person_dimensions(
        request.transparency_summary,
        findings_text=(
            request.direct_answer,
            request.executive_summary,
            *request.analytical_findings,
        ),
    )

_COUNT_WORDS = {
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
}


def _split_finding_summary(summary: str) -> tuple[str, str]:
    if ": " in summary:
        title, description = summary.split(": ", 1)
        return title, description
    return summary, summary


_TRANSPARENCY_METRIC_LINE_PREFIXES = (
    "Temporal filter:",
    "Period:",
    "Date column:",
    "Records analysed:",
    "Highest:",
    "Lowest:",
    "Metrics analysed:",
    "Snapshot:",
    "Applied filter:",
    "Reason:",
    "Analysis:",
)


def _translate_executive_text(
    text: str,
    *,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> str:
    return translator.translate_prose(text, person_dimensions=person_dimensions)


def _strip_analytical_title(title: str) -> str:
    normalized = title.strip().rstrip(".")
    lower = normalized.lower()
    for prefix in _ANALYTICAL_TITLE_PREFIXES:
        if lower == prefix or lower.startswith(f"{prefix}:"):
            return ""
    return normalized


def _parse_operational_assessment(
    operational_assessment: str | None,
    *,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> tuple[str | None, str | None]:
    if not operational_assessment:
        return None, None
    if ": " in operational_assessment:
        level, rationale = operational_assessment.split(": ", 1)
        return (
            translator.translate_identifier(level),
            _translate_executive_text(
                rationale,
                translator=translator,
                person_dimensions=person_dimensions,
            ),
        )
    return None, _translate_executive_text(
        operational_assessment,
        translator=translator,
        person_dimensions=person_dimensions,
    )


def _extract_investigation_targets(
    transparency_summary: tuple[str, ...],
    translator: BusinessNarrativeTranslator,
) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()
    for line in translator.filter_transparency_lines(transparency_summary):
        if not line.startswith("Dimension: "):
            continue
        target = translator.translate_identifier(line.removeprefix("Dimension: "))
        key = target.lower()
        if not target or key in seen:
            continue
        seen.add(key)
        targets.append(target)
    return tuple(targets)


def _extract_metrics_from_transparency(
    transparency_summary: tuple[str, ...],
    translator: BusinessNarrativeTranslator,
) -> tuple[str, ...]:
    metrics: list[str] = []
    seen: set[str] = set()
    for line in translator.filter_transparency_lines(transparency_summary):
        if line.startswith("Dimension: "):
            continue
        if any(line.startswith(prefix) for prefix in _TRANSPARENCY_METRIC_LINE_PREFIXES):
            continue
        candidate = translator.translate_identifier(line.strip())
        if not candidate or candidate.startswith("-"):
            continue
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        metrics.append(candidate)
    return tuple(metrics)


def _extract_affected_metrics(
    request: NarrativeRequest,
    *,
    investigation_targets: tuple[str, ...],
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> tuple[str, ...]:
    dimension_names = {target.lower() for target in investigation_targets}
    combined_text = "\n".join(
        (
            request.direct_answer,
            request.executive_summary,
            *request.analytical_findings,
        )
    )
    seen: set[str] = set()
    metrics: list[str] = []

    for label in _extract_metrics_from_transparency(request.transparency_summary, translator):
        if label.lower() in dimension_names:
            continue
        key = label.lower()
        if key not in seen:
            seen.add(key)
            metrics.append(label)

    for identifier in (
        *extract_quoted_identifiers(combined_text),
        *extract_snake_case_identifiers(combined_text),
    ):
        if translator.registry.is_person_dimension(identifier):
            continue
        if identifier.lower().replace(" ", "_") in {
            "anomaly_detection",
            "variance_analysis",
            "trend_analysis",
            "snapshot_analysis",
        }:
            continue
        label = translator.translate_identifier(identifier)
        key = label.lower()
        if key in seen or key in dimension_names:
            continue
        seen.add(key)
        metrics.append(label)

    for finding in request.analytical_findings:
        title, _ = _split_finding_summary(finding)
        stripped_title = _strip_analytical_title(title)
        if not stripped_title:
            continue
        title_text = _translate_executive_text(
            stripped_title,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        if not title_text or is_analytical_telemetry(title_text) or is_implementation_title(title_text):
            continue
        key = title_text.lower()
        if key in seen or key in dimension_names:
            continue
        seen.add(key)
        metrics.append(title_text)

    return tuple(metrics)


def _format_list(items: tuple[str, ...]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _count_word(count: int) -> str:
    return _COUNT_WORDS.get(count, str(count))


def _meaningful_severity_phrase(executive_severity: str | None) -> str:
    if not executive_severity:
        return ""
    level = executive_severity.lower()
    if level in {"critical", "high", "medium"}:
        return f"{level} "
    return ""


def _is_substantive_direct_answer(text: str) -> bool:
    stripped = text.strip()
    if not stripped or is_analytical_telemetry(stripped):
        return False
    if any(character.isdigit() for character in stripped):
        return True
    return len(stripped.split()) >= 10


def _build_key_message(
    *,
    affected_metrics: tuple[str, ...],
    executive_severity: str | None,
    direct_answer_summary: str,
    operational_significance: str | None,
) -> str:
    if direct_answer_summary and _is_substantive_direct_answer(direct_answer_summary):
        return direct_answer_summary

    if operational_significance and not is_analytical_telemetry(operational_significance):
        return operational_significance

    severity_phrase = _meaningful_severity_phrase(executive_severity)

    if len(affected_metrics) > 1:
        metric_text = _format_list(affected_metrics)
        return (
            f"{_count_word(len(affected_metrics))} {severity_phrase}operational metrics "
            f"({metric_text}) show performance materially outside normal expectations "
            "and require investigation."
        ).replace("  ", " ")

    if len(affected_metrics) == 1:
        return (
            f"{affected_metrics[0]} shows {severity_phrase}performance materially outside "
            "normal expectations and requires investigation."
        ).replace("  ", " ")

    if direct_answer_summary and not is_analytical_telemetry(direct_answer_summary):
        return direct_answer_summary

    if severity_phrase:
        return (
            f"{severity_phrase.strip().capitalize()} operational performance requires "
            "executive review based on the deterministic analysis."
        )

    return "Operational performance requires executive review based on the deterministic analysis."


_BANNER_INDICATORS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "stable": "🟢",
}

_CONFIDENCE_INDICATORS = {
    "High": "🟢",
    "Medium": "🟡",
    "Low": "🟡",
}


def _build_executive_assessment(
    *,
    executive_severity: str | None,
    finding_count: int,
    affected_metrics: tuple[str, ...],
) -> tuple[str, str, str]:
    if finding_count == 0 and executive_severity is None:
        return (
            "stable",
            _BANNER_INDICATORS["stable"],
            "Operational performance appears stable. No significant issues detected.",
        )

    severity = (executive_severity or "").lower()
    if severity == "critical" or (severity == "high" and len(affected_metrics) >= 2):
        if len(affected_metrics) >= 2:
            headline = (
                "Multiple critical operational metrics require immediate investigation."
            )
        else:
            headline = "Critical operational performance requires immediate investigation."
        return ("critical", _BANNER_INDICATORS["critical"], headline)

    if severity == "high":
        return (
            "high",
            _BANNER_INDICATORS["high"],
            "High-priority operational metrics require immediate investigation.",
        )

    if severity == "medium" or finding_count > 0:
        return (
            "medium",
            _BANNER_INDICATORS["medium"],
            "Moderate operational risks detected. Targeted investigation recommended.",
        )

    return (
        "stable",
        _BANNER_INDICATORS["stable"],
        "Operational performance appears stable. No significant issues detected.",
    )


def _build_assessment_confidence(
    *,
    finding_count: int,
    affected_metrics: tuple[str, ...],
    executive_severity: str | None,
    has_operational_assessment: bool,
) -> tuple[str, str]:
    confidence_signals = 0
    if finding_count >= 2:
        confidence_signals += 1
    if len(affected_metrics) >= 2:
        confidence_signals += 1
    if executive_severity and executive_severity.lower() in {"critical", "high"}:
        confidence_signals += 1
    if has_operational_assessment:
        confidence_signals += 1

    if confidence_signals >= 3 or (finding_count >= 2 and len(affected_metrics) >= 2):
        return (
            "High",
            "Multiple independent analytical signals identified consistent findings.",
        )

    if confidence_signals >= 2 or (finding_count >= 1 and has_operational_assessment):
        return (
            "Medium",
            "Findings are supported by reported evidence across the analysis.",
        )

    return (
        "Medium",
        "Findings are based on limited evidence and should be interpreted alongside supporting detail.",
    )


def _build_why_this_matters(
    *,
    finding_count: int,
) -> str:
    if finding_count > 0:
        return (
            "These findings indicate that current reported performance may not accurately "
            "represent operational conditions. Review the Direct Answer and Priority Actions "
            "before making significant operational or strategic decisions."
        )

    return (
        "Review the Direct Answer and supporting evidence before making significant "
        "operational or strategic decisions."
    )


def _build_prioritized_explanations(
    *,
    affected_metrics: tuple[str, ...],
    finding_count: int,
    investigation_targets: tuple[str, ...],
) -> str:
    multi_metric = len(affected_metrics) >= 2
    multi_finding = finding_count >= 2
    has_dimension = bool(investigation_targets)

    if multi_metric and (multi_finding or len(affected_metrics) >= 3) and not has_dimension:
        return (
            "Based on the available evidence, the most plausible explanations are "
            "organisation-wide reporting inconsistencies or cross-cutting operational effects, "
            "because anomalies appear across multiple unrelated operational metrics. "
            "Treat this as a hypothesis until validated."
        )

    if has_dimension:
        target_text = _format_list(investigation_targets)
        return (
            f"Based on the available evidence, the most plausible explanations are "
            f"localised operational issues within affected {target_text}, rather than "
            "organisation-wide effects. Treat this as a hypothesis until validated."
        )

    if multi_metric:
        return (
            "Based on the available evidence, the most plausible explanations include "
            "reporting inconsistencies or operational changes affecting multiple metrics. "
            "The available evidence cannot distinguish between these causes — validate before deciding."
        )

    return (
        "Based on the available evidence, the most plausible explanations include "
        "operational disruption, process changes, or data quality issues. "
        "The available evidence cannot distinguish between these causes — validate before deciding."
    )


def _build_investigation_strategy(
    *,
    investigation_targets: tuple[str, ...],
    affected_metrics: tuple[str, ...],
    finding_count: int,
) -> str:
    parts: list[str] = []

    if investigation_targets:
        target_text = _format_list(investigation_targets)
        parts.append(
            f"Start by comparing results across {target_text} to see whether the pattern "
            "is localised or widespread."
        )
        parts.append(
            "If the pattern is concentrated, investigate local operational causes in the "
            "affected areas first."
        )
    else:
        parts.append(
            "Begin by determining whether the issue is isolated to a particular operational area, "
            "concentrated within specific dimensions, or widespread across the dataset."
        )
        if finding_count > 1 or len(affected_metrics) > 1:
            parts.append(
                "Review whether the pattern clusters within specific areas or appears across "
                "unrelated parts of the operation."
            )
        else:
            parts.append(
                "Review the primary answer and supporting evidence to confirm where the pattern "
                "is most pronounced before expanding the investigation."
            )

    return " ".join(parts)


def _build_executive_actions(
    request: NarrativeRequest,
    *,
    investigation_targets: tuple[str, ...],
    affected_metrics: tuple[str, ...],
    finding_count: int,
    executive_severity: str | None,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> tuple[str, ...]:
    actions: list[str] = []

    def add_action(action: str) -> None:
        normalized = action.strip().rstrip(".")
        if not normalized:
            return
        normalized_lower = normalized.lower()
        if any(existing.lower().rstrip(".") == normalized_lower for existing in actions):
            return
        actions.append(f"{normalized}.")

    for action in request.priority_actions:
        translated = _translate_executive_text(
            action,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        if translated:
            add_action(translated)

    if actions:
        return tuple(actions[:3])

    if investigation_targets:
        target_text = _format_list(investigation_targets)
        add_action(
            f"Compare results across {target_text} to confirm where the pattern is concentrated"
        )
    elif affected_metrics:
        add_action(
            f"Review {_format_list(affected_metrics[:2])} using the Direct Answer and "
            "supporting evidence"
        )

    if executive_severity and executive_severity.lower() in {"critical", "high"} and finding_count > 0:
        add_action("Confirm high-priority findings before making operational commitments")

    if not actions:
        add_action(
            "Review the Direct Answer and supporting evidence before deciding next steps"
        )

    return tuple(actions)


def _build_operational_investigation_actions(
    request: NarrativeRequest,
    *,
    affected_metrics: tuple[str, ...],
    executive_actions: tuple[str, ...],
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> tuple[str, ...]:
    actions: list[str] = []
    executive_normalized = {
        action.lower().rstrip(".") for action in executive_actions
    }

    def add_action(action: str) -> None:
        normalized = action.strip().rstrip(".")
        if not normalized:
            return
        normalized_lower = normalized.lower()
        if normalized_lower in executive_normalized:
            return
        if any(existing.lower().rstrip(".") == normalized_lower for existing in actions):
            return
        actions.append(f"{normalized}.")

    for metric in affected_metrics:
        add_action(f"Review {metric} records for supporting detail")

    if not actions and request.analytical_findings:
        add_action("Review supporting analytical evidence linked to the priority action")

    return tuple(actions)


def _to_business_implication(description: str) -> str:
    cleaned = description.strip().rstrip(".")
    if not cleaned or is_analytical_telemetry(cleaned):
        return ""
    return (
        "The evidence suggests performance may be materially outside normal expectations "
        f"where {cleaned}."
    )


def _build_business_implications(
    request: NarrativeRequest,
    *,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> tuple[str, ...]:
    implications: list[str] = []
    seen: set[str] = set()

    for finding in request.analytical_findings:
        title, description = _split_finding_summary(finding)
        description_text = _translate_executive_text(
            description,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        if description_text and not is_analytical_telemetry(description_text):
            implication = _to_business_implication(description_text)
        else:
            title_text = _strip_analytical_title(
                _translate_executive_text(
                    title,
                    translator=translator,
                    person_dimensions=person_dimensions,
                )
            )
            implication = _to_business_implication(title_text) if title_text else ""

        if implication and implication.lower() not in seen:
            seen.add(implication.lower())
            implications.append(implication)

    return tuple(implications)


def _build_business_summary(
    request: NarrativeRequest,
    *,
    key_message: str,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> str:
    translated_summary = _translate_executive_text(
        request.executive_summary,
        translator=translator,
        person_dimensions=person_dimensions,
    )
    if translated_summary and not is_analytical_telemetry(translated_summary):
        return translated_summary
    return key_message


def _build_direct_answer_summary(
    request: NarrativeRequest,
    *,
    translator: BusinessNarrativeTranslator,
    person_dimensions: tuple[str, ...],
) -> str:
    translated = _translate_executive_text(
        collapse_multiline_text(request.direct_answer),
        translator=translator,
        person_dimensions=person_dimensions,
    )
    substantive_sentences = [
        sentence
        for sentence in split_sentences(translated)
        if sentence and not is_analytical_telemetry(sentence)
    ]
    if substantive_sentences:
        return " ".join(substantive_sentences[:2])

    if translated and not is_analytical_telemetry(translated):
        return translated

    return "The analysis indicates a substantive pattern that should be reviewed in context."


def _build_business_impact(
    *,
    executive_severity: str | None,
    finding_count: int,
) -> str | None:
    if executive_severity and executive_severity.lower() in {"critical", "high"}:
        return (
            "Operational reporting may not accurately reflect current performance until "
            "this pattern is understood."
        )

    if finding_count > 0:
        return "This pattern should be reviewed before operational decisions are made."

    return None


def _build_decision_guidance(*, executive_severity: str | None) -> str | None:
    if executive_severity and executive_severity.lower() in {"critical", "high"}:
        return "Defer major operational commitments until the cause is validated."
    return None


class ExecutiveContextBuilder:
    """Build domain-agnostic executive context from completed narrative requests."""

    def __init__(self, translator: BusinessNarrativeTranslator | None = None) -> None:
        self._translator = translator or _DEFAULT_TRANSLATOR

    def build(self, request: NarrativeRequest) -> ExecutiveContext:
        """Return translated executive context without modifying source evidence."""
        translator = self._translator
        person_dimensions = _person_dimensions_for_request(request, translator)
        executive_severity, assessment_significance = _parse_operational_assessment(
            request.operational_assessment,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        investigation_targets = _extract_investigation_targets(
            request.transparency_summary,
            translator,
        )
        affected_metrics = _extract_affected_metrics(
            request,
            investigation_targets=investigation_targets,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        finding_count = len(request.analytical_findings)
        direct_answer_summary = _build_direct_answer_summary(
            request,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        key_message = _build_key_message(
            affected_metrics=affected_metrics,
            executive_severity=executive_severity,
            direct_answer_summary=direct_answer_summary,
            operational_significance=assessment_significance,
        )
        assessment_level, assessment_indicator, assessment_headline = _build_executive_assessment(
            executive_severity=executive_severity,
            finding_count=finding_count,
            affected_metrics=affected_metrics,
        )
        confidence_level, confidence_rationale = _build_assessment_confidence(
            finding_count=finding_count,
            affected_metrics=affected_metrics,
            executive_severity=executive_severity,
            has_operational_assessment=assessment_significance is not None,
        )
        why_this_matters = _build_why_this_matters(finding_count=finding_count)
        executive_actions = _build_executive_actions(
            request,
            investigation_targets=investigation_targets,
            affected_metrics=affected_metrics,
            finding_count=finding_count,
            executive_severity=executive_severity,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        operational_investigation_actions = _build_operational_investigation_actions(
            request,
            affected_metrics=affected_metrics,
            executive_actions=executive_actions,
            translator=translator,
            person_dimensions=person_dimensions,
        )
        prioritized_explanations = _build_prioritized_explanations(
            affected_metrics=affected_metrics,
            finding_count=finding_count,
            investigation_targets=investigation_targets,
        )
        conclusions = tuple(
            _translate_executive_text(
                conclusion,
                translator=translator,
                person_dimensions=person_dimensions,
            )
            for conclusion in request.executive_conclusions
            if _translate_executive_text(
                conclusion,
                translator=translator,
                person_dimensions=person_dimensions,
            )
        )

        return ExecutiveContext(
            question=request.question,
            key_message=key_message,
            executive_assessment_level=assessment_level,
            executive_assessment_indicator=assessment_indicator,
            executive_assessment_headline=assessment_headline,
            assessment_confidence_level=confidence_level,
            assessment_confidence_rationale=confidence_rationale,
            business_summary=_build_business_summary(
                request,
                key_message=key_message,
                translator=translator,
                person_dimensions=person_dimensions,
            ),
            direct_answer_summary=direct_answer_summary,
            why_this_matters=why_this_matters,
            key_findings=_build_business_implications(
                request,
                translator=translator,
                person_dimensions=person_dimensions,
            ),
            operational_significance=assessment_significance,
            executive_severity=executive_severity,
            business_impact=_build_business_impact(
                executive_severity=executive_severity,
                finding_count=finding_count,
            ),
            decision_guidance=_build_decision_guidance(executive_severity=executive_severity),
            investigation_strategy=_build_investigation_strategy(
                investigation_targets=investigation_targets,
                affected_metrics=affected_metrics,
                finding_count=finding_count,
            ),
            prioritized_explanations=prioritized_explanations,
            conclusions=conclusions,
            executive_actions=executive_actions,
            operational_investigation_actions=operational_investigation_actions,
            investigation_targets=investigation_targets,
            investigation_categories=DEFAULT_INVESTIGATION_CATEGORIES,
            affected_metrics=affected_metrics,
        )
