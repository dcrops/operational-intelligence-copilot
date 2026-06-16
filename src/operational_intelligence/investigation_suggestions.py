"""Deterministic follow-up investigation suggestions derived from findings."""

from __future__ import annotations

from src.operational_intelligence.models import Finding

FINDING_TYPE_ORDER = ("anomaly", "variance", "trend")

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

_HUMILITY_VERBS = ("investigate", "review", "explore", "examine", "may warrant")

_CAUSATION_BLACKLIST = (
    "caused by",
    "because of",
    "due to",
    "proves",
    "responsible for",
    "root cause",
)


def _finding_type(finding: Finding) -> str | None:
    title = finding.title.lower()
    if "anomaly" in title:
        return "anomaly"
    if "variance" in title:
        return "variance"
    if "trend" in title:
        return "trend"
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
            if _looks_like_period_key(key, value):
                continue
            return key
    return None


def _has_group_metadata(finding: Finding) -> bool:
    return _extract_dimension_column(finding) is not None


def _trend_label(finding: Finding) -> str | None:
    for item in finding.evidence:
        label = item.supporting_context.get("trend_label")
        if label is not None:
            return str(label).lower()
    return None


def _comparison_direction(finding: Finding) -> str | None:
    for item in finding.evidence:
        direction = item.supporting_context.get("comparison_direction")
        if direction is not None:
            return str(direction).lower()
    return None


def _validate_suggestion(text: str) -> str:
    lowered = text.lower()
    if not any(verb in lowered for verb in _HUMILITY_VERBS):
        raise ValueError(f"Suggestion missing humble wording: {text!r}")
    for phrase in _CAUSATION_BLACKLIST:
        if phrase in lowered:
            raise ValueError(
                f"Suggestion contains disallowed causation phrase {phrase!r}: {text!r}"
            )
    return text


class InvestigationSuggestionGenerator:
    """Generate domain-agnostic follow-up investigation prompts from findings."""

    def generate_for_finding(self, finding: Finding) -> list[str]:
        finding_type = _finding_type(finding)
        if finding_type == "trend":
            return self._trend_suggestions(finding)
        if finding_type == "variance":
            return self._variance_suggestions(finding)
        if finding_type == "anomaly":
            return self._anomaly_suggestions(finding)
        return []

    def generate_for_findings(self, findings: list[Finding]) -> list[str]:
        typed_findings = [
            (index, finding)
            for index, finding in enumerate(findings)
            if _finding_type(finding) is not None
        ]
        typed_findings.sort(
            key=lambda pair: (FINDING_TYPE_ORDER.index(_finding_type(pair[1])), pair[0])
        )

        suggestions: list[str] = []
        seen: set[str] = set()
        for _, finding in typed_findings:
            for suggestion in self.generate_for_finding(finding):
                if suggestion not in seen:
                    suggestions.append(suggestion)
                    seen.add(suggestion)
        return suggestions

    def _trend_suggestions(self, finding: Finding) -> list[str]:
        metric = _metric_label(finding)
        suggestions = [
            _validate_suggestion(
                f"Investigate whether {metric} changes are concentrated in specific periods."
            ),
        ]

        if _has_group_metadata(finding):
            suggestions.append(
                _validate_suggestion(
                    f"Review which groups contributed most to the change in {metric}."
                )
            )
        else:
            suggestions.append(
                _validate_suggestion(
                    "Review whether particular groups contributed disproportionately "
                    "to the observed change."
                )
            )

        suggestions.append(
            _validate_suggestion(
                "Explore whether related metrics also changed over the same period."
            )
        )

        if _trend_label(finding) == "volatile":
            suggestions.append(
                _validate_suggestion(
                    f"Examine whether short-term volatility in {metric} may warrant "
                    "further review."
                )
            )

        return suggestions

    def _variance_suggestions(self, finding: Finding) -> list[str]:
        metric = _metric_label(finding)
        dimension_column = _extract_dimension_column(finding)

        if dimension_column:
            dimension = _humanize(dimension_column)
            suggestions = [
                _validate_suggestion(
                    f"Review which {dimension} values contributed most to the "
                    f"difference in {metric}."
                ),
            ]
        else:
            suggestions = [
                _validate_suggestion(
                    "Review whether particular groups contributed disproportionately "
                    "to the observed difference."
                ),
            ]

        suggestions.extend(
            [
                _validate_suggestion(
                    "Examine whether this difference has changed over time."
                ),
                _validate_suggestion(
                    "Explore whether related metrics are also elevated for the "
                    "highlighted group."
                ),
            ]
        )

        if _comparison_direction(finding) == "dual":
            suggestions.append(
                _validate_suggestion(
                    "Investigate whether the gap between the highest and lowest groups "
                    "may warrant further review."
                )
            )

        return suggestions

    def _anomaly_suggestions(self, finding: Finding) -> list[str]:
        metric = _metric_label(finding)
        return [
            _validate_suggestion(
                f"Investigate whether anomalies in {metric} are clustered by group."
            ),
            _validate_suggestion(
                "Review whether anomalies are concentrated in specific time periods."
            ),
            _validate_suggestion(
                "Examine whether the same records appear unusual across multiple metrics."
            ),
        ]
