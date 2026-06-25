"""Tests for the Business Narrative Translation Layer."""

from __future__ import annotations

from src.operational_intelligence.llm.business_narrative_translation import (
    BusinessNarrativeTranslator,
    TranslationCategory,
    TranslationRegistry,
    TranslatedIdentifier,
)


def _translator() -> BusinessNarrativeTranslator:
    return BusinessNarrativeTranslator()


class TestPreserve:
    def test_business_metrics_remain_unchanged(self) -> None:
        translator = _translator()

        assert translator.translate_identifier("attendance_rate") == "Attendance Rate"
        assert translator.translate_identifier("Attendance Rate") == "Attendance Rate"
        assert translator.translate_identifier("overtime_hours") == "Overtime Hours"

    def test_operational_entities_remain_unchanged(self) -> None:
        translator = _translator()

        assert translator.abstract_entity_reference("Line B", "production_line") == "Line B"
        assert translator.abstract_entity_reference("School C", "school") == "School C"
        assert (
            translator.abstract_entity_reference("Finance Department", "department")
            == "Finance Department"
        )
        assert (
            translator.abstract_entity_reference("Melbourne Branch", "branch_code")
            == "Melbourne Branch"
        )
        assert translator.abstract_entity_reference("Region North", "region") == "Region North"


class TestTranslate:
    def test_known_identifier_mappings(self) -> None:
        translator = _translator()

        assert translator.translate_identifier("employee_name") == "Employee"
        assert translator.translate_identifier("department_name") == "Department"
        assert translator.translate_identifier("student_name") == "Student"
        assert translator.translate_identifier("patient_name") == "Patient"
        assert translator.translate_identifier("branch_code") == "Branch"
        assert translator.translate_identifier("production_line") == "Production Line"
        assert translator.translate_identifier("anomaly_detection") == "Performance anomalies"
        assert translator.translate_identifier("variance_analysis") == "Performance comparison"

    def test_technical_prose_is_translated(self) -> None:
        translator = _translator()
        translated = translator.translate_prose(
            "Line B: defects = 52, compared with an average of 8.2 (z-score 5.08)."
        )

        assert "z-score" not in translated.lower()
        assert "far outside the normal operating range" in translated.lower()

    def test_registry_supports_plural_terminology(self) -> None:
        entry = TranslationRegistry.default().lookup_terminology("employee_name")

        assert entry is not None
        assert entry.singular == "Employee"
        assert entry.plural == "Employees"
        assert entry.label(plural=True) == "Employees"


class TestRemove:
    def test_transparency_metadata_is_removed(self) -> None:
        translator = _translator()
        lines = (
            "Metric selected: Overtime Hours",
            "Metric inferred: Absence Days",
            "Dimension selected: department",
            "Dimension inferred: employee_name",
            "Aggregation inferred: sum",
            "Aggregation selected: mean",
            "Comparison direction inferred: highest",
            "Comparison direction selected: lowest",
            "Comparison inferred: highest",
            "Analysis type selected: variance_analysis",
            "Date column selected: month",
            "Routed tools: anomaly_detection",
            "Findings returned: 2",
            "Clarification: resolved",
            "Automatically resolved: metric",
        )

        for line in lines:
            assert translator.classify_transparency_line(line) == TranslationCategory.REMOVE

        filtered = translator.filter_transparency_lines(lines)
        assert filtered == ()

    def test_removed_metadata_never_appears_in_prose(self) -> None:
        translator = _translator()
        prose = translator.translate_prose(
            "Metric selected: Overtime Hours. Aggregation inferred: sum. "
            "Comparison inferred: highest."
        )

        assert "Metric selected" not in prose
        assert "Aggregation inferred" not in prose
        assert "Comparison inferred" not in prose


class TestAbstract:
    def test_person_names_become_executive_safe_labels(self) -> None:
        translator = _translator()

        assert (
            translator.abstract_entity_reference("Hayden King", "employee_name")
            == "Individual employee"
        )
        assert (
            translator.abstract_entity_reference("Hayden King", "student_name")
            == "Individual student"
        )

    def test_person_names_in_prose_are_abstracted(self) -> None:
        translator = _translator()
        prose = translator.translate_prose(
            "Hayden King shows overtime materially outside normal expectations.",
            person_dimensions=("employee_name",),
        )

        assert "Hayden King" not in prose
        assert "Individual employee" in prose


class TestOrderingAndIdentity:
    def test_translate_ordered_concepts_preserves_order(self) -> None:
        translator = _translator()
        concepts = (
            "Attendance Rate",
            "employee_name",
            "Aggregation inferred: sum",
            "Comparison inferred: highest",
            "Hayden King",
            "Department",
        )

        translated = translator.translate_ordered_concepts(
            concepts,
            person_dimensions=("employee_name",),
        )

        assert translated == ("Attendance Rate", "Employee", "Department")

    def test_translate_identifier_with_source_retains_internal_identity(self) -> None:
        translator = _translator()
        translated = translator.translate_identifier_with_source("employee_name")

        assert isinstance(translated, TranslatedIdentifier)
        assert translated.source == "employee_name"
        assert translated.display == "Employee"
        assert translated.category == TranslationCategory.TRANSLATE


class TestEndToEndTranslationRegression:
    def test_mixed_artefacts_produce_executive_safe_output(self) -> None:
        translator = _translator()
        concepts = (
            "Attendance Rate",
            "employee_name",
            "Aggregation inferred: sum",
            "Comparison inferred: highest",
            "Hayden King",
            "department_name",
        )

        translated = translator.translate_ordered_concepts(
            concepts,
            person_dimensions=("employee_name",),
        )

        assert translated == ("Attendance Rate", "Employee", "Department")
        assert "Hayden King" not in translated
        assert "Aggregation inferred" not in " ".join(translated)
        assert "Comparison inferred" not in " ".join(translated)

    def test_reasoning_trace_theme_labels_are_translated(self) -> None:
        translator = _translator()
        trace = (
            "Theme 1: overtime_hours",
            "Theme 2: anomaly_detection",
            "Assessment: Defect load requires immediate review.",
        )

        translated = translator.translate_reasoning_trace(trace)

        assert translated[0] == "Theme 1: Overtime Hours"
        assert translated[1] == "Theme 2: Performance anomalies"
        assert "Defect load requires immediate review." in translated[2]
