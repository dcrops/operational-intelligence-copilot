"""Registry-backed translation from deterministic artefacts to executive language."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

_SNAKE_CASE_PATTERN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
_ANALYZED_COLUMN_PATTERN = re.compile(
    r"Analyzed column '([^']+)' for anomalies using z-score threshold [^.\n]+\.\s*",
    re.IGNORECASE,
)
_Z_SCORE_PAREN_PATTERN = re.compile(
    r"\(\s*z-score\s+[-+]?\d+(?:\.\d+)?\s*\)",
    re.IGNORECASE,
)
_Z_SCORE_INLINE_PATTERN = re.compile(
    r"\bz-score\s+[-+]?\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
_Z_SCORE_THRESHOLD_PATTERN = re.compile(
    r"z-score threshold\s+[-+]?\d+(?:\.\d+)?",
    re.IGNORECASE,
)
_IMPLEMENTATION_TOOL_PATTERN = re.compile(r"\s+tool\b", re.IGNORECASE)
_ANALYTICAL_TELEMETRY_PATTERNS = (
    re.compile(r"Operational analysis identified[^.]*\.\s*", re.IGNORECASE),
    re.compile(
        r"\d+\s+unusual\s+(?:high|low\s+)?values?\s+were\s+detected[^.]*\.\s*",
        re.IGNORECASE,
    ),
    re.compile(r"Unusual values were identified for[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Examples include:\s*", re.IGNORECASE),
    re.compile(r"Affected records:\s*", re.IGNORECASE),
    re.compile(r"See supporting evidence for[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"\bfinding\(s\)\b", re.IGNORECASE),
    re.compile(
        r"\b\d+\s+additional\s+unusual\s+records?\s+were\s+also\s+identified\.?\s*",
        re.IGNORECASE,
    ),
)
_ORPHAN_NUMBER_FRAGMENT = re.compile(r"\.\s+\d+\.(?:\s|$)")
_BULLET_PREFIX = re.compile(r"^\s*-\s*", re.MULTILINE)
_FINDING_TITLE_TOOL_PATTERNS = (
    re.compile(r"^Anomalies Detected by .+$", re.IGNORECASE),
    re.compile(r"^Significant Variance Identified by .+$", re.IGNORECASE),
    re.compile(r"^Trend Identified by .+$", re.IGNORECASE),
    re.compile(r"^Snapshot Summary from .+$", re.IGNORECASE),
    re.compile(r"^Analysis Failure(?: Linked)?(?: to .+)?$", re.IGNORECASE),
)
_PERSON_NAME_IN_PROSE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")


class TranslationCategory(str, Enum):
    """Classification for analytical artefacts in executive narrative output."""

    PRESERVE = "preserve"
    TRANSLATE = "translate"
    REMOVE = "remove"
    ABSTRACT = "abstract"


@dataclass(frozen=True)
class TerminologyEntry:
    """Business terminology with optional plural form for future extension."""

    singular: str
    plural: str | None = None

    def label(self, *, plural: bool = False) -> str:
        if plural and self.plural:
            return self.plural
        return self.singular


@dataclass(frozen=True)
class TranslatedIdentifier:
    """Presentation label with retained source identifier for traceability."""

    source: str
    display: str
    category: TranslationCategory


@dataclass(frozen=True)
class TranslationRegistry:
    """Declarative rules for business narrative translation."""

    terminology: dict[str, TerminologyEntry]
    person_dimensions: dict[str, str]
    transparency_remove_prefixes: tuple[str, ...]
    prose_remove_patterns: tuple[re.Pattern[str], ...]
    prose_translate_patterns: tuple[tuple[re.Pattern[str], str], ...]
    operational_dimension_keys: frozenset[str]

    @classmethod
    def default(cls) -> TranslationRegistry:
        terminology = {
            "employee_name": TerminologyEntry("Employee", "Employees"),
            "department_name": TerminologyEntry("Department", "Departments"),
            "student_name": TerminologyEntry("Student", "Students"),
            "patient_name": TerminologyEntry("Patient", "Patients"),
            "customer_name": TerminologyEntry("Customer", "Customers"),
            "person_name": TerminologyEntry("Person", "People"),
            "branch_code": TerminologyEntry("Branch", "Branches"),
            "production_line": TerminologyEntry("Production Line", "Production Lines"),
            "attendance_rate": TerminologyEntry("Attendance Rate"),
            "overtime_hours": TerminologyEntry("Overtime Hours"),
            "behaviour_incidents": TerminologyEntry("Behaviour Incidents"),
            "behaviour_incident": TerminologyEntry("Behaviour Incidents"),
            "anomaly_detection": TerminologyEntry("Performance anomalies"),
            "variance_analysis": TerminologyEntry("Performance comparison"),
            "department": TerminologyEntry("Department", "Departments"),
        }

        person_dimensions = {
            "employee_name": "Individual employee",
            "student_name": "Individual student",
            "patient_name": "Individual patient",
            "customer_name": "Individual customer",
            "person_name": "Individual person",
        }

        transparency_remove_prefixes = (
            "Metric selected:",
            "Metric inferred:",
            "Dimension selected:",
            "Dimension inferred:",
            "Aggregation inferred:",
            "Aggregation selected:",
            "Comparison direction inferred:",
            "Comparison direction selected:",
            "Comparison inferred:",
            "Comparison selected:",
            "Analysis type selected:",
            "Date column selected:",
            "Routed tools:",
            "Findings returned:",
            "Clarification:",
            "Clarifications:",
            "Automatically resolved:",
        )

        prose_remove_patterns = _ANALYTICAL_TELEMETRY_PATTERNS + (
            re.compile(r"\busing z-score method\b", re.IGNORECASE),
            re.compile(r"\bdetected using z-score\b", re.IGNORECASE),
            re.compile(r"Metric selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Metric inferred:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Dimension selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Dimension inferred:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Aggregation inferred:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Aggregation selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Comparison direction inferred:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Comparison direction selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Comparison inferred:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Comparison selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Analysis type selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Date column selected:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Routed tools:\s*[^.]+\.?\s*", re.IGNORECASE),
            re.compile(r"Findings returned:\s*[^.]+\.?\s*", re.IGNORECASE),
        )

        prose_translate_patterns = (
            (_ANALYZED_COLUMN_PATTERN, "{metric} appears outside normal expectations. "),
            (_Z_SCORE_PAREN_PATTERN, "(far outside the normal operating range)"),
            (_Z_SCORE_INLINE_PATTERN, "result far outside the normal operating range"),
            (_Z_SCORE_THRESHOLD_PATTERN, "expected operating range"),
            (re.compile(r"\bstandard deviation\b", re.IGNORECASE), "expected variation"),
            (re.compile(r"\banomaly threshold\b", re.IGNORECASE), "expected operating range"),
            (re.compile(r"\banomaly detection\b", re.IGNORECASE), "performance anomalies"),
            (re.compile(r"\bvariance analysis\b", re.IGNORECASE), "performance comparison"),
            (re.compile(r"\banomalous records?\b", re.IGNORECASE), "unusual records"),
            (
                re.compile(r"\bunusual value identification\b", re.IGNORECASE),
                "unusual performance pattern",
            ),
            (
                re.compile(r"\boperational analysis identified\b", re.IGNORECASE),
                "The analysis indicates",
            ),
            (
                re.compile(
                    r"\b\d+\s+unusual\s+(?:high|low\s+)?values?\s+were\s+detected\b",
                    re.IGNORECASE,
                ),
                "Performance appears outside normal expectations",
            ),
            (
                re.compile(r"Anomalies Detected by .+", re.IGNORECASE),
                "Significant performance anomalies",
            ),
            (
                re.compile(r"Significant Variance Identified by .+", re.IGNORECASE),
                "Significant performance differences",
            ),
            (re.compile(r"Trend Identified by .+", re.IGNORECASE), "Significant performance trends"),
            (
                re.compile(r"Snapshot Summary from .+", re.IGNORECASE),
                "Snapshot performance summary",
            ),
        )

        operational_dimension_keys = frozenset(
            {
                "production_line",
                "department",
                "department_name",
                "branch_code",
                "school",
                "region",
                "location",
                "campus",
            }
        )

        return cls(
            terminology=terminology,
            person_dimensions=person_dimensions,
            transparency_remove_prefixes=transparency_remove_prefixes,
            prose_remove_patterns=prose_remove_patterns,
            prose_translate_patterns=prose_translate_patterns,
            operational_dimension_keys=operational_dimension_keys,
        )

    def lookup_terminology(self, identifier: str) -> TerminologyEntry | None:
        key = identifier.strip().lower().replace(" ", "_")
        return self.terminology.get(key)

    def is_person_dimension(self, dimension: str | None) -> bool:
        if not dimension:
            return False
        return dimension.strip().lower().replace(" ", "_") in self.person_dimensions

    def is_operational_dimension(self, dimension: str | None) -> bool:
        if not dimension:
            return False
        return dimension.strip().lower().replace(" ", "_") in self.operational_dimension_keys


class BusinessNarrativeTranslator:
    """Convert deterministic analytical artefacts into executive business language."""

    def __init__(self, registry: TranslationRegistry | None = None) -> None:
        self._registry = registry or TranslationRegistry.default()

    @property
    def registry(self) -> TranslationRegistry:
        return self._registry

    def classify_transparency_line(self, line: str) -> TranslationCategory:
        stripped = line.strip()
        if not stripped:
            return TranslationCategory.REMOVE

        lower = stripped.lower()
        for prefix in self._registry.transparency_remove_prefixes:
            if lower.startswith(prefix.lower()):
                return TranslationCategory.REMOVE

        if stripped.startswith("Dimension: "):
            return TranslationCategory.TRANSLATE

        if any(
            stripped.startswith(prefix)
            for prefix in (
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
        ):
            return TranslationCategory.PRESERVE

        if _SNAKE_CASE_PATTERN.search(stripped):
            return TranslationCategory.TRANSLATE

        return TranslationCategory.PRESERVE

    def filter_transparency_lines(
        self,
        lines: Iterable[str],
    ) -> tuple[str, ...]:
        """Drop removed transparency lines while preserving deterministic order."""
        filtered: list[str] = []
        for line in lines:
            if self.classify_transparency_line(line) == TranslationCategory.REMOVE:
                continue
            filtered.append(line)
        return tuple(filtered)

    def translate_identifier_with_source(self, identifier: str) -> TranslatedIdentifier:
        cleaned = identifier.strip()
        if not cleaned:
            return TranslatedIdentifier("", "", TranslationCategory.REMOVE)

        key = cleaned.lower().replace(" ", "_")
        entry = self._registry.lookup_terminology(key)
        if entry:
            return TranslatedIdentifier(cleaned, entry.singular, TranslationCategory.TRANSLATE)

        if self._registry.is_person_dimension(cleaned):
            return TranslatedIdentifier(
                cleaned,
                self._registry.person_dimensions[key],
                TranslationCategory.ABSTRACT,
            )

        if _SNAKE_CASE_PATTERN.fullmatch(cleaned):
            display = " ".join(word.capitalize() for word in cleaned.split("_"))
            return TranslatedIdentifier(cleaned, display, TranslationCategory.TRANSLATE)

        if cleaned.islower() and cleaned.isalpha():
            display = cleaned.capitalize()
            return TranslatedIdentifier(cleaned, display, TranslationCategory.TRANSLATE)

        return TranslatedIdentifier(cleaned, cleaned, TranslationCategory.PRESERVE)

    def translate_identifier(self, identifier: str) -> str:
        return self.translate_identifier_with_source(identifier).display

    def abstract_entity_reference(self, name: str, dimension: str | None) -> str:
        cleaned = name.strip()
        if not cleaned:
            return cleaned

        if self._registry.is_operational_dimension(dimension):
            return cleaned

        if self._registry.is_person_dimension(dimension):
            key = dimension.strip().lower().replace(" ", "_")
            return self._registry.person_dimensions[key]

        return cleaned

    def translate_reasoning_trace(self, lines: Iterable[str]) -> tuple[str, ...]:
        translated: list[str] = []
        for line in lines:
            if line.startswith("Theme "):
                prefix, _, remainder = line.partition(": ")
                theme_label = remainder.strip()
                translated.append(f"{prefix}: {self.translate_identifier(theme_label)}")
                continue
            if line.startswith("Assessment: "):
                translated.append(
                    f"Assessment: {self.translate_prose(line.removeprefix('Assessment: '))}"
                )
                continue
            translated.append(self.translate_prose(line))
        return tuple(translated)

    def translate_prose(
        self,
        text: str,
        *,
        person_dimensions: Iterable[str] = (),
    ) -> str:
        if not text.strip():
            return text

        cleaned = collapse_multiline_text(text)
        for pattern in self._registry.prose_remove_patterns:
            cleaned = pattern.sub("", cleaned)

        for pattern, replacement in self._registry.prose_translate_patterns:
            if "{metric}" in replacement:
                cleaned = pattern.sub(
                    lambda match, repl=replacement: repl.format(
                        metric=self.translate_identifier(match.group(1))
                    ),
                    cleaned,
                )
            else:
                cleaned = pattern.sub(replacement, cleaned)

        cleaned = _IMPLEMENTATION_TOOL_PATTERN.sub("", cleaned)
        cleaned = self._translate_embedded_identifiers(cleaned)
        cleaned = self._abstract_person_names_in_prose(
            cleaned,
            person_dimensions=tuple(person_dimensions),
        )
        cleaned = sanitize_executive_prose(cleaned)
        return cleaned.strip()

    def translate_ordered_concepts(
        self,
        concepts: Iterable[str],
        *,
        person_dimensions: Iterable[str] = (),
    ) -> tuple[str, ...]:
        """Translate an ordered list of mixed artefacts for executive presentation."""
        person_dims = tuple(person_dimensions)
        output: list[str] = []
        seen: set[str] = set()

        for concept in concepts:
            stripped = concept.strip()
            if not stripped:
                continue

            if self.classify_transparency_line(stripped) == TranslationCategory.REMOVE:
                continue

            if stripped.startswith("Dimension: "):
                raw = stripped.removeprefix("Dimension: ").strip()
                label = self.translate_identifier(raw)
            elif _looks_like_person_name(stripped) and person_dims and any(
                self._registry.is_person_dimension(dim) for dim in person_dims
            ):
                continue
            else:
                translated = self.translate_identifier_with_source(stripped)
                if translated.category == TranslationCategory.REMOVE:
                    continue
                label = translated.display

            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(label)

        return tuple(output)

    def extract_person_dimensions(
        self,
        transparency_summary: Iterable[str],
        *,
        findings_text: Iterable[str] = (),
    ) -> tuple[str, ...]:
        """Return person-identifying dimensions found in transparency or findings."""
        dimensions: list[str] = []
        seen: set[str] = set()

        for line in transparency_summary:
            if not line.startswith("Dimension: "):
                continue
            raw = line.removeprefix("Dimension: ").strip()
            key = raw.lower().replace(" ", "_")
            if self._registry.is_person_dimension(raw) and key not in seen:
                seen.add(key)
                dimensions.append(raw)

        for text in findings_text:
            for identifier in extract_snake_case_identifiers(text):
                if self._registry.is_person_dimension(identifier):
                    key = identifier.lower()
                    if key not in seen:
                        seen.add(key)
                        dimensions.append(identifier)

        return tuple(dimensions)

    def _translate_embedded_identifiers(self, text: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            return self.translate_identifier(match.group(0))

        return _SNAKE_CASE_PATTERN.sub(replacer, text)

    def _abstract_person_names_in_prose(
        self,
        text: str,
        *,
        person_dimensions: tuple[str, ...],
    ) -> str:
        if not person_dimensions or not any(
            self._registry.is_person_dimension(dim) for dim in person_dimensions
        ):
            return text

        person_dim = next(
            dim for dim in person_dimensions if self._registry.is_person_dimension(dim)
        )
        abstract_label = self.abstract_entity_reference("placeholder", person_dim)

        def replace_highest_lowest(match: re.Match[str]) -> str:
            prefix = match.group(1)
            entity = match.group(2).strip()
            value = match.group(3)
            if self._registry.is_operational_dimension(person_dim):
                return match.group(0)
            if _looks_like_person_name(entity):
                return f"{prefix}{abstract_label} ({value})"
            return match.group(0)

        text = re.sub(
            r"((?:Highest|Lowest):\s*)([^()]+?)\s*(\([^)]+\))",
            replace_highest_lowest,
            text,
        )

        for match in _PERSON_NAME_IN_PROSE_PATTERN.finditer(text):
            name = match.group(0)
            if not _looks_like_person_name(name):
                continue
            text = text.replace(name, abstract_label)

        return text


def collapse_multiline_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    return " ".join(lines)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def sanitize_executive_prose(text: str) -> str:
    if not text.strip():
        return text

    cleaned = _BULLET_PREFIX.sub("", text)
    cleaned = _ORPHAN_NUMBER_FRAGMENT.sub(". ", cleaned)
    cleaned = re.sub(r"([A-Za-z])\.\s+(\d+)\.$", r"\1.", cleaned)
    cleaned = re.sub(r"\s+\.", ".", cleaned)
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+,", ",", cleaned)
    return cleaned.strip()


def is_implementation_title(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if _IMPLEMENTATION_TOOL_PATTERN.search(cleaned):
        return True
    return any(pattern.match(cleaned) for pattern in _FINDING_TITLE_TOOL_PATTERNS)


def is_analytical_telemetry(text: str) -> bool:
    lower = text.lower().strip()
    if not lower:
        return True
    telemetry_markers = (
        "operational analysis identified",
        "finding(s)",
        "examples include",
        "affected records",
        "unusual values were identified for",
        "were detected for",
        "high priority",
        "medium priority",
        "low priority",
        "metric selected:",
        "aggregation inferred:",
        "comparison inferred:",
        "comparison direction inferred:",
        "routed tools:",
    )
    return any(marker in lower for marker in telemetry_markers)


def extract_quoted_identifiers(text: str) -> tuple[str, ...]:
    seen: set[str] = set()
    identifiers: list[str] = []
    quoted_pattern = re.compile(r"'([^']+)'")
    for match in quoted_pattern.finditer(text):
        identifier = match.group(1).strip()
        if not identifier:
            continue
        key = identifier.lower()
        if key in seen:
            continue
        seen.add(key)
        identifiers.append(identifier)
    return tuple(identifiers)


def extract_snake_case_identifiers(text: str) -> tuple[str, ...]:
    seen: set[str] = set()
    identifiers: list[str] = []
    for match in _SNAKE_CASE_PATTERN.finditer(text):
        identifier = match.group(0)
        key = identifier.lower()
        if key in seen:
            continue
        seen.add(key)
        identifiers.append(identifier)
    return tuple(identifiers)


def _looks_like_person_name(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned or cleaned.lower() in {
        "attendance rate",
        "overtime hours",
        "behaviour incidents",
        "production line",
        "finance department",
        "melbourne branch",
        "region north",
        "line b",
        "school c",
    }:
        return False
    return bool(_PERSON_NAME_IN_PROSE_PATTERN.fullmatch(cleaned))
