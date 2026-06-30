"""Deterministic follow-up investigation suggestions derived from findings."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.operational_intelligence.models import DatasetProfile, Finding
from src.operational_intelligence.question_semantics import (
    has_anomaly_intent,
    has_trend_intent,
    resolve_comparison_direction,
)
from src.operational_intelligence.schema_resolution import is_identifier_column, non_identifier_dimensions

FINDING_TYPE_ORDER = ("anomaly", "variance", "trend", "snapshot", "failure")
MAX_FOLLOW_UP_SUGGESTIONS = 3

SUPPORTED_SUGGESTION_TOOLS = (
    "trend_analysis",
    "variance_analysis",
    "anomaly_detection",
    "risk_assessment",
)

_METADATA_KEYS = frozenset(
    {
        "row_index",
        "mean",
        "standard_deviation",
        "z_score",
        "anomaly_direction",
        "aggregation",
        "comparison_direction",
        "comparison_extreme",
        "is_comparison_target",
        "trend_label",
        "n_periods",
        "pct_change",
        "pct_change_percent",
        "normalized_slope",
        "reversals",
        "positive_steps",
        "negative_steps",
        "cv",
        "range_ratio",
    }
)

_HUMILITY_VERBS = ("investigate", "review", "explore", "examine", "may warrant", "show", "list")

_DIRECT_QUESTION_PREFIXES = ("how ", "what ", "which ", "show ", "list ", "compare ")

_CAUSATION_BLACKLIST = (
    "caused by",
    "because of",
    "due to",
    "proves",
    "responsible for",
    "root cause",
)

_BANNED_SUGGESTION_PATTERNS = (
    "related metrics",
    "particular groups",
    "clustered by group",
    "specific time periods",
    "multiple metrics",
    "also elevated",
    "records contributing most",
    "unusual values",
    "contributed most",
    "contributing records",
    "contributing factors",
    "concentrated in periods",
    "concentrated in specific",
    "concentrated by group",
    "identify drivers",
    "explain why",
    "causal analysis",
    "clustering behaviour",
    "clustering behavior",
    "underlying causes",
    "gap between the highest and lowest",
    "short-term volatility",
    "may warrant further review",
    "compares to the dataset baseline",
)


@dataclass(frozen=True)
class SuggestionCapabilityContext:
    """Dataset and tool context for capability-aware follow-up generation."""

    profile: DatasetProfile | None = None

    def has_tool(self, tool_name: str) -> bool:
        if self.profile is None:
            return True
        return tool_name in self.profile.suitable_tools

    def has_dimensions(self) -> bool:
        if self.profile is None:
            return True
        return bool(self.profile.potential_dimensions)

    def has_date_columns(self) -> bool:
        if self.profile is None:
            return True
        return bool(self.profile.date_columns)

    def dimension_supported(self, column: str | None) -> bool:
        if not column:
            return False
        if self.profile is None:
            return True
        return column in self.profile.potential_dimensions

    def preferred_dimension(self, finding: Finding) -> str | None:
        evidence_dimension = _extract_dimension_column(finding)
        if evidence_dimension and self.dimension_supported(evidence_dimension):
            if self.profile is None or not is_identifier_column(evidence_dimension):
                return evidence_dimension
        if self.profile and self.profile.potential_dimensions:
            for dimension in non_identifier_dimensions(self.profile.potential_dimensions):
                if self.dimension_supported(dimension):
                    return dimension
        return None


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


def _humanize(text: str) -> str:
    return text.replace("_", " ")


def _metric_label(finding: Finding) -> str:
    for item in finding.evidence:
        if item.metric_name:
            return _humanize(item.metric_name)
    return "the metric"


def _looks_like_period_key(key: str, value: object) -> bool:
    key_lower = key.lower()
    if "date" in key_lower or key_lower.endswith("_at"):
        return True
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return True
    return False


def _extract_dimension_column(finding: Finding) -> str | None:
    for item in finding.evidence:
        for key, value in item.supporting_context.items():
            if key in _METADATA_KEYS or value is None:
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                continue
            if _looks_like_period_key(key, value):
                continue
            return key
    return None


def _comparison_direction(finding: Finding) -> str | None:
    for item in finding.evidence:
        direction = item.supporting_context.get("comparison_direction")
        if direction is not None:
            return str(direction).lower()
    return None


def _validate_suggestion(text: str) -> str:
    lowered = text.lower().strip()
    is_direct_capability_question = lowered.startswith(_DIRECT_QUESTION_PREFIXES)
    if not is_direct_capability_question and not any(
        verb in lowered for verb in _HUMILITY_VERBS
    ):
        raise ValueError(f"Suggestion missing supported question wording: {text!r}")
    for phrase in _CAUSATION_BLACKLIST:
        if phrase in lowered:
            raise ValueError(
                f"Suggestion contains disallowed causation phrase {phrase!r}: {text!r}"
            )
    for pattern in _BANNED_SUGGESTION_PATTERNS:
        if pattern in lowered:
            raise ValueError(f"Suggestion contains banned pattern {pattern!r}: {text!r}")
    return text


def classify_suggestion_capability(text: str) -> str | None:
    """Return the analytical tool a follow-up suggestion maps to, if determinable."""
    lowered = text.lower().strip()
    if lowered.startswith("show unusual ") or lowered.startswith("list unusual "):
        return "anomaly_detection"
    if lowered.startswith("show the anomalous") or lowered.startswith("list the anomalous"):
        return "anomaly_detection"
    if lowered.endswith(" are unusual?") and lowered.startswith("which "):
        return "anomaly_detection"
    if lowered.startswith("how has ") and " changed over time" in lowered:
        return "trend_analysis"
    if lowered.startswith("show the ") and lowered.endswith(" trend."):
        return "trend_analysis"
    if lowered.startswith("what is the overall trend in "):
        return "trend_analysis"
    if lowered.startswith("which ") and " has the highest " in lowered:
        return "variance_analysis"
    if lowered.startswith("which ") and " has the lowest " in lowered:
        return "variance_analysis"
    if lowered.startswith("compare ") and " across " in lowered:
        return "variance_analysis"
    if "findings require immediate attention" in lowered or "highest priority findings" in lowered:
        return "risk_assessment"
    if lowered.startswith("what findings should be reviewed"):
        return "risk_assessment"
    return None


def normalize_question_for_comparison(text: str) -> str:
    """Normalize question text for lightweight duplicate detection."""
    normalized = text.lower().strip().replace("_", " ")
    normalized = re.sub(r"[^\w\s]", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def is_equivalent_question(candidate: str, original: str | None) -> bool:
    """Return True when candidate and original ask the same investigation."""
    if not original or not original.strip():
        return False
    return normalize_question_for_comparison(candidate) == normalize_question_for_comparison(
        original
    )


def original_redundant_with_suggestion(original: str | None, suggestion: str) -> bool:
    """Return True when a follow-up would repeat the user's original investigation."""
    if not original or not original.strip():
        return False
    if is_equivalent_question(suggestion, original):
        return True

    capability = classify_suggestion_capability(suggestion)
    if capability == "trend_analysis" and has_trend_intent(original):
        return True
    if capability == "anomaly_detection" and has_anomaly_intent(original):
        return True
    return False


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def filter_duplicate_priority_actions(
    suggestions: list[str],
    priority_action_texts: list[str],
) -> list[str]:
    """Remove follow-ups that substantially repeat Priority Action text."""
    priority_phrases = [_normalize_text(text) for text in priority_action_texts if text.strip()]
    filtered: list[str] = []
    for suggestion in suggestions:
        normalized = _normalize_text(suggestion)
        if any(
            phrase and (phrase in normalized or normalized in phrase)
            for phrase in priority_phrases
        ):
            continue
        filtered.append(suggestion)
    return filtered


def _trend_question(metric: str) -> str:
    return _validate_suggestion(f"How has {metric} changed over time?")


def _variance_question(metric: str, dimension: str, comparison_direction: str | None) -> str:
    dimension_label = _humanize(dimension)
    if comparison_direction == "bottom":
        return _validate_suggestion(f"Which {dimension_label} has the lowest {metric}?")
    if comparison_direction == "dual":
        return _validate_suggestion(f"Compare {metric} across {dimension_label}.")
    return _validate_suggestion(f"Which {dimension_label} has the highest {metric}?")


def _anomaly_question(metric: str) -> str:
    return _validate_suggestion(f"Show unusual {metric} records.")


def _risk_question() -> str:
    return _validate_suggestion("What findings should be reviewed?")


class InvestigationSuggestionGenerator:
    """Generate capability-aware follow-up investigation prompts from findings."""

    def __init__(self, capability: SuggestionCapabilityContext | None = None) -> None:
        self._capability = capability or SuggestionCapabilityContext()

    def generate_for_finding(
        self,
        finding: Finding,
        *,
        original_question: str | None = None,
    ) -> list[str]:
        return self._progression_candidates(finding, original_question)

    def generate_for_findings(
        self,
        findings: list[Finding],
        *,
        profile: DatasetProfile | None = None,
        original_question: str | None = None,
    ) -> list[str]:
        capability = SuggestionCapabilityContext(
            profile=profile or self._capability.profile,
        )
        generator = InvestigationSuggestionGenerator(capability)

        typed_findings = [
            (index, finding)
            for index, finding in enumerate(findings)
            if _resolve_finding_type(finding) is not None
        ]
        typed_findings.sort(
            key=lambda pair: (FINDING_TYPE_ORDER.index(_resolve_finding_type(pair[1])), pair[0])
        )

        suggestions: list[str] = []
        seen: set[str] = set()
        for _, finding in typed_findings:
            for suggestion in generator._progression_candidates(finding, original_question):
                if suggestion in seen:
                    continue
                if original_redundant_with_suggestion(original_question, suggestion):
                    continue
                suggestions.append(suggestion)
                seen.add(suggestion)
                if len(suggestions) >= MAX_FOLLOW_UP_SUGGESTIONS:
                    return suggestions

        if not suggestions and findings:
            for suggestion in generator._safe_fallback_suggestions(findings, original_question):
                if suggestion in seen:
                    continue
                if original_redundant_with_suggestion(original_question, suggestion):
                    continue
                suggestions.append(suggestion)
                seen.add(suggestion)
                if len(suggestions) >= MAX_FOLLOW_UP_SUGGESTIONS:
                    break

        return suggestions[:MAX_FOLLOW_UP_SUGGESTIONS]

    def _alternate_dimensions(self, primary_dimension: str | None) -> list[str]:
        if not self._capability.profile or not self._capability.profile.potential_dimensions:
            return []
        dimensions = non_identifier_dimensions(self._capability.profile.potential_dimensions)
        return [
            dimension
            for dimension in dimensions
            if dimension != primary_dimension and self._capability.dimension_supported(dimension)
        ]

    def _append_candidate(self, candidates: list[str], candidate: str | None) -> None:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    def _maybe_trend_question(self, metric: str) -> str | None:
        if not self._capability.has_tool("trend_analysis") or not self._capability.has_date_columns():
            return None
        return _trend_question(metric)

    def _maybe_anomaly_question(self, metric: str) -> str | None:
        if not self._capability.has_tool("anomaly_detection"):
            return None
        return _anomaly_question(metric)

    def _maybe_variance_question(
        self,
        metric: str,
        dimension: str | None,
        comparison_direction: str | None,
    ) -> str | None:
        if not dimension or not self._capability.has_tool("variance_analysis"):
            return None
        if not self._capability.dimension_supported(dimension):
            return None
        return _variance_question(metric, dimension, comparison_direction)

    def _maybe_risk_question(self) -> str | None:
        if not self._capability.has_tool("risk_assessment"):
            return None
        return _risk_question()

    def _progression_candidates(
        self,
        finding: Finding,
        original_question: str | None,
    ) -> list[str]:
        finding_type = _resolve_finding_type(finding)
        metric = _metric_label(finding)
        dimension = _extract_dimension_column(finding) or self._capability.preferred_dimension(
            finding
        )
        original_direction = (
            resolve_comparison_direction(original_question) if original_question else None
        )
        finding_direction = _comparison_direction(finding)
        candidates: list[str] = []

        if finding_type == "variance":
            if not dimension:
                return []

            self._append_candidate(
                candidates,
                self._maybe_variance_question(metric, dimension, finding_direction),
            )

            if finding_direction == "top" or original_direction == "top":
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "bottom"),
                )
                self._append_candidate(candidates, self._maybe_trend_question(metric))
                self._append_candidate(candidates, self._maybe_anomaly_question(metric))
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "dual"),
                )
            elif finding_direction == "bottom" or original_direction == "bottom":
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "top"),
                )
                self._append_candidate(candidates, self._maybe_trend_question(metric))
                self._append_candidate(candidates, self._maybe_anomaly_question(metric))
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "dual"),
                )
            else:
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "top"),
                )
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "bottom"),
                )
                self._append_candidate(candidates, self._maybe_trend_question(metric))
                self._append_candidate(candidates, self._maybe_anomaly_question(metric))

            for alternate_dimension in self._alternate_dimensions(dimension):
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, alternate_dimension, "dual"),
                )

        elif finding_type == "trend":
            self._append_candidate(candidates, self._maybe_trend_question(metric))
            if dimension:
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "top"),
                )
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "bottom"),
                )
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "dual"),
                )
            self._append_candidate(candidates, self._maybe_anomaly_question(metric))

        elif finding_type == "anomaly":
            self._append_candidate(candidates, self._maybe_anomaly_question(metric))
            if dimension:
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "top"),
                )
                self._append_candidate(
                    candidates,
                    self._maybe_variance_question(metric, dimension, "bottom"),
                )
            self._append_candidate(candidates, self._maybe_trend_question(metric))
            self._append_candidate(candidates, self._maybe_risk_question())

        return candidates

    def _safe_fallback_suggestions(
        self,
        findings: list[Finding],
        original_question: str | None = None,
    ) -> list[str]:
        for finding in findings:
            for suggestion in self._progression_candidates(finding, original_question):
                if not original_redundant_with_suggestion(original_question, suggestion):
                    return [suggestion]
        return []
