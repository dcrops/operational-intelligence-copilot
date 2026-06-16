from src.operational_intelligence.schema_resolution import (
    is_identifier_column,
    non_identifier_dimensions,
    resolve_dimension_from_question,
    resolve_metric_from_question,
    select_variance_dimension,
)


MANUFACTURING_METRICS = ["defects", "downtime_minutes", "units_produced"]
MANUFACTURING_DIMENSIONS = [
    "production_line",
    "shift",
    "site",
    "supervisor",
    "employee_id",
]
WORKFORCE_METRICS = ["hours", "overtime_hours", "absence_days"]
WORKFORCE_DIMENSIONS = [
    "employee_id",
    "employee_name",
    "department",
    "location",
    "manager",
    "employment_type",
]


def test_resolve_downtime_minutes_underscore_form():
    question = "How has downtime_minutes changed over time?"
    assert resolve_metric_from_question(question, MANUFACTURING_METRICS) == "downtime_minutes"


def test_resolve_downtime_minutes_space_form():
    question = "How has downtime minutes changed over time?"
    assert resolve_metric_from_question(question, MANUFACTURING_METRICS) == "downtime_minutes"


def test_resolve_production_line_and_defects():
    question = "Which production line has the highest defects?"
    assert (
        resolve_dimension_from_question(question, MANUFACTURING_DIMENSIONS)
        == "production_line"
    )
    assert resolve_metric_from_question(question, MANUFACTURING_METRICS) == "defects"


def test_resolve_department_and_hours():
    question = "Which department has the highest hours?"
    assert resolve_dimension_from_question(question, WORKFORCE_DIMENSIONS) == "department"
    assert resolve_metric_from_question(question, WORKFORCE_METRICS) == "hours"


def test_resolve_metric_returns_none_for_generic_question():
    question = "What looks unusual?"
    assert resolve_metric_from_question(question, MANUFACTURING_METRICS) is None


def test_identifier_dimensions_are_not_selected_unless_explicit():
    question = "Which group has the highest values?"
    fallback = select_variance_dimension(question, WORKFORCE_DIMENSIONS)
    assert fallback == "employee_name"
    assert "employee_id" not in non_identifier_dimensions(WORKFORCE_DIMENSIONS)


def test_identifier_dimension_can_be_selected_when_explicit():
    question = "Compare totals by employee_id"
    assert resolve_dimension_from_question(question, WORKFORCE_DIMENSIONS) == "employee_id"


def test_longest_metric_match_is_preferred():
    metrics = ["downtime", "downtime_minutes"]
    question = "How has downtime_minutes changed over time?"
    assert resolve_metric_from_question(question, metrics) == "downtime_minutes"


def test_is_identifier_column_recognizes_common_patterns():
    assert is_identifier_column("employee_id") is True
    assert is_identifier_column("transaction_id") is True
    assert is_identifier_column("department") is False
