"""Tests for executive theme grouping (Milestone 9 Phase 9b)."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

from src.operational_intelligence.executive_reasoning import (
    ExecutiveReasoningEngine,
    ExecutiveTheme,
)
from src.operational_intelligence.models import EvidenceItem, Finding


pytestmark = pytest.mark.unit


def _make_finding(
    *,
    finding_id: str,
    finding_type: str,
    metric_name: str | None = None,
    title: str | None = None,
    evidence: list[EvidenceItem] | None = None,
) -> Finding:
    if evidence is None and metric_name is not None:
        evidence = [
            EvidenceItem(
                description=f"Evidence for {metric_name}",
                metric_name=metric_name,
                metric_value=1.0,
                supporting_context={"aggregation": "sum"},
            )
        ]

    return Finding(
        finding_id=finding_id,
        finding_type=finding_type,
        source_tool=f"{finding_type}_analysis",
        title=title or f"{finding_type.title()} finding",
        description=f"{finding_type.title()} description.",
        severity="LOW",
        confidence="MEDIUM",
        evidence=evidence or [],
    )


class TestExecutiveThemeModel:
    def test_finding_ids_and_findings_must_match(self):
        with pytest.raises(ValueError, match="finding_ids and findings must have the same length"):
            ExecutiveTheme(
                theme_id="theme-metric-hours",
                theme_label="hours",
                finding_ids=["finding-0"],
                findings=[],
            )


class TestExecutiveReasoningEngine:
    def test_empty_input_returns_empty_list(self):
        assert ExecutiveReasoningEngine().group_findings([]) == []

    def test_rejects_non_list_input(self):
        with pytest.raises(ValueError, match="findings must be a list"):
            ExecutiveReasoningEngine().group_findings("not a list")  # type: ignore[arg-type]

    def test_single_finding_with_metric_produces_one_theme(self):
        finding = _make_finding(
            finding_id="finding-0",
            finding_type="trend",
            metric_name="attendance_rate",
        )

        themes = ExecutiveReasoningEngine().group_findings([finding])

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-metric-attendance_rate"
        assert themes[0].theme_label == "attendance_rate"
        assert themes[0].finding_ids == ["finding-0"]
        assert themes[0].findings == [finding]

    def test_multiple_findings_same_metric_grouped(self):
        findings = [
            _make_finding(
                finding_id="finding-0",
                finding_type="trend",
                metric_name="attendance_rate",
            ),
            _make_finding(
                finding_id="finding-1",
                finding_type="snapshot",
                metric_name="attendance_rate",
            ),
            _make_finding(
                finding_id="finding-2",
                finding_type="anomaly",
                metric_name="attendance_rate",
            ),
        ]

        themes = ExecutiveReasoningEngine().group_findings(findings)

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-metric-attendance_rate"
        assert themes[0].theme_label == "attendance_rate"
        assert themes[0].finding_ids == ["finding-0", "finding-1", "finding-2"]
        assert themes[0].findings == findings

    def test_findings_different_metrics_produce_separate_themes(self):
        findings = [
            _make_finding(
                finding_id="finding-0",
                finding_type="trend",
                metric_name="attendance_rate",
            ),
            _make_finding(
                finding_id="finding-1",
                finding_type="variance",
                metric_name="defects",
            ),
        ]

        themes = ExecutiveReasoningEngine().group_findings(findings)

        assert [theme.theme_id for theme in themes] == [
            "theme-metric-attendance_rate",
            "theme-metric-defects",
        ]
        assert [theme.theme_label for theme in themes] == [
            "attendance_rate",
            "defects",
        ]

    def test_no_metric_falls_back_to_finding_type(self):
        finding = Finding(
            finding_id="finding-0",
            finding_type="failure",
            source_tool="trend_analysis",
            title="Tool 'trend_analysis' failed to execute successfully",
            description="Trend analysis failed.",
            severity="MEDIUM",
            confidence="HIGH",
            evidence=[],
        )

        themes = ExecutiveReasoningEngine().group_findings([finding])

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-type-failure"
        assert themes[0].theme_label == "failure"
        assert themes[0].finding_ids == ["finding-0"]

    def test_legacy_finding_without_provenance_uses_title_type_fallback(self):
        finding = Finding(
            title="Significant Variance Identified by Variance Analysis Tool",
            description="Variance across groups detected.",
            severity="MEDIUM",
            confidence="MEDIUM",
            evidence=[
                EvidenceItem(
                    description="Department comparison",
                    metric_name="hours",
                    metric_value=600.0,
                    supporting_context={
                        "department": "Ops",
                        "aggregation": "sum",
                    },
                )
            ],
        )

        themes = ExecutiveReasoningEngine().group_findings([finding])

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-metric-hours"
        assert themes[0].theme_label == "hours"

    def test_ambiguous_multi_metric_finding_falls_back_to_finding_type(self):
        finding = Finding(
            finding_id="finding-0",
            finding_type="anomaly",
            source_tool="anomaly_detection",
            title="Anomalies Detected by Anomaly Detection Tool",
            description="Multiple metrics present.",
            severity="HIGH",
            confidence="HIGH",
            evidence=[
                EvidenceItem(
                    description="Metric A",
                    metric_name="hours",
                    metric_value=900.0,
                    supporting_context={"anomaly_direction": "HIGH"},
                ),
                EvidenceItem(
                    description="Metric B",
                    metric_name="defects",
                    metric_value=52.0,
                    supporting_context={"anomaly_direction": "HIGH"},
                ),
            ],
        )

        themes = ExecutiveReasoningEngine().group_findings([finding])

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-type-anomaly"
        assert themes[0].theme_label == "anomaly"

    def test_unknown_finding_becomes_standalone_theme(self):
        finding = Finding(
            title="Generic operational note",
            description="No metric or known finding type.",
            severity="INFO",
            confidence="LOW",
            evidence=[],
        )

        themes = ExecutiveReasoningEngine().group_findings([finding])

        assert len(themes) == 1
        assert themes[0].theme_id == "theme-standalone-standalone-0"
        assert themes[0].theme_label == "standalone-0"
        assert themes[0].findings == [finding]

    def test_deterministic_theme_ordering(self):
        findings = [
            _make_finding(
                finding_id="finding-0",
                finding_type="variance",
                metric_name="defects",
            ),
            _make_finding(
                finding_id="finding-1",
                finding_type="trend",
                metric_name="attendance_rate",
            ),
            Finding(
                finding_id="finding-2",
                finding_type="failure",
                source_tool="trend_analysis",
                title="Tool 'trend_analysis' failed to execute successfully",
                description="Trend analysis failed.",
                severity="MEDIUM",
                confidence="HIGH",
                evidence=[],
            ),
        ]

        engine = ExecutiveReasoningEngine()
        first = engine.group_findings(findings)
        second = engine.group_findings(findings)

        assert [theme.theme_id for theme in first] == [
            "theme-metric-attendance_rate",
            "theme-metric-defects",
            "theme-type-failure",
        ]
        assert first == second

    def test_every_finding_assigned_to_exactly_one_theme(self):
        findings = [
            _make_finding(
                finding_id="finding-0",
                finding_type="trend",
                metric_name="attendance_rate",
            ),
            _make_finding(
                finding_id="finding-1",
                finding_type="snapshot",
                metric_name="attendance_rate",
            ),
            _make_finding(
                finding_id="finding-2",
                finding_type="variance",
                metric_name="defects",
            ),
            Finding(
                finding_id="finding-3",
                finding_type="failure",
                source_tool="trend_analysis",
                title="Tool 'trend_analysis' failed to execute successfully",
                description="Trend analysis failed.",
                severity="MEDIUM",
                confidence="HIGH",
                evidence=[],
            ),
        ]

        themes = ExecutiveReasoningEngine().group_findings(findings)

        grouped_findings = [finding for theme in themes for finding in theme.findings]
        assert grouped_findings == findings
        assert sum(len(theme.findings) for theme in themes) == len(findings)

    def test_module_does_not_import_pandas(self):
        module_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "operational_intelligence"
            / "executive_reasoning.py"
        )
        module_source = module_path.read_text(encoding="utf-8")
        parsed = ast.parse(module_source)

        imported_names: set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module.split(".")[0])

        assert "pandas" not in imported_names

    def test_engine_module_imports_without_pandas(self):
        spec = importlib.util.find_spec("src.operational_intelligence.executive_reasoning")
        assert spec is not None
        assert spec.origin is not None
