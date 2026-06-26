"""Golden dataset and question registry for application journey tests.

Defines expected *behaviour* only — not exact rendered text or analytical values.
Future milestones (10d+) add journey tests that reference these entries.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ui.executive_reasoning_presentation import (
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
    EXECUTIVE_REASONING_HEADING,
)
from ui.results_headings import (
    ANALYSIS_HEADER_STATUS,
    SECTION_AUDIT,
    SECTION_INVESTIGATION,
    SECTION_OVERVIEW,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample"


class ExpectedOutcome(str, Enum):
    """High-level application outcome after a question is submitted."""

    RESULTS = "results"
    CLARIFICATION = "clarification"


# User-visible report section titles (behavioural anchors, not output text).
SECTION_DIRECT_ANSWER = "Direct Answer"
SECTION_OPERATIONAL_ASSESSMENT = "Operational Assessment"
SECTION_SYSTEM_TRANSPARENCY = "System Transparency"
SECTION_CLARIFICATION = "Clarification Required"
SECTION_RESULTS = ANALYSIS_HEADER_STATUS

STANDARD_RESULTS_SECTIONS: tuple[str, ...] = (
    SECTION_DIRECT_ANSWER,
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
)

EXECUTIVE_REASONING_SECTIONS: tuple[str, ...] = (
    EXECUTIVE_REASONING_HEADING,
    SECTION_OPERATIONAL_ASSESSMENT,
)

SECTION_EXECUTIVE_CONCLUSIONS = "Executive Conclusions"
SECTION_PRIORITY_ACTIONS = "Priority Actions"

FULL_EXECUTIVE_REASONING_SECTIONS: tuple[str, ...] = (
    *EXECUTIVE_REASONING_SECTIONS,
    SECTION_EXECUTIVE_CONCLUSIONS,
    SECTION_PRIORITY_ACTIONS,
)

SNAPSHOT_TRANSPARENCY_MARKER = "Snapshot mode activated:"
TEMPORAL_FILTER_MARKER = "Applied temporal filter:"
SNAPSHOT_CONTRIBUTORS_MARKER = "Snapshot contributors:"

SECTION_DATASET_PREVIEW = "Dataset Preview"
SECTION_EXECUTIVE_SUMMARY = "Executive Summary"
SECTION_AI_ASSISTED_EXECUTIVE_NARRATIVE = SECTION_EXECUTIVE_SUMMARY
NARRATIVE_DISABLED_MARKER = "Executive summary is unavailable"
PROFILE_SUMMARY_HEADING = "Profile summary"
LOAD_SUCCESS_MARKER = "Loaded"
INVALID_EMPTY_CSV_MARKER = "uploaded CSV is empty"

APP_SHELL_TITLE = "Operational Intelligence Copilot"
APP_SHELL_BRAND = "CHASE RISK & COMPLIANCE"
APP_SHELL_SIDEBAR_PLATFORM = "Operational Intelligence Platform"
APP_SHELL_SUBTITLE_FRAGMENT = "Transform operational data into trusted executive decisions"
APP_SHELL_BADGE_FRAGMENT = "Evidence-Based Analytics"


@dataclass(frozen=True)
class GoldenDataset:
    """Committed CSV regression asset metadata."""

    registry_name: str
    csv_path: Path
    domain: str
    role: str
    sidebar_label: str | None = None
    app_dataset_name: str | None = None


@dataclass(frozen=True)
class ClarificationStep:
    """Expected clarification interaction before results can appear."""

    clarification_type: str
    option: str | None = None


@dataclass(frozen=True)
class GoldenQuestion:
    """Reusable golden question with behavioural expectations."""

    question: str
    expected_outcome: ExpectedOutcome
    visible_sections: tuple[str, ...] = ()
    clarification_type: str | None = None
    clarification_steps: tuple[ClarificationStep, ...] = ()
    expects_snapshot: bool = False
    expects_temporal_filter: bool = False
    expects_snapshot_contributors: bool = False
    notes: str = ""


@dataclass(frozen=True)
class GoldenScenario:
    """Dataset + question pairing for AppTest and future Playwright journeys."""

    scenario_id: str
    dataset: GoldenDataset
    question: GoldenQuestion
    description: str = ""
    follow_up_question: GoldenQuestion | None = None
    replacement_dataset: GoldenDataset | None = None
    replacement_question: GoldenQuestion | None = None
    invalid_fixture_path: Path | None = None
    invalid_error_marker: str = ""


GOLDEN_DATASETS: dict[str, GoldenDataset] = {
    "manufacturing_demo": GoldenDataset(
        registry_name="manufacturing_demo",
        csv_path=SAMPLE_DATA_DIR / "manufacturing_demo.csv",
        domain="Manufacturing",
        role="primary",
        sidebar_label="Manufacturing demo",
        app_dataset_name="manufacturing_demo",
    ),
    "education_demo": GoldenDataset(
        registry_name="education_demo",
        csv_path=SAMPLE_DATA_DIR / "education_demo.csv",
        domain="Education",
        role="primary",
        sidebar_label="Education demo",
        app_dataset_name="education_demo",
    ),
    "workforce_demo_v2": GoldenDataset(
        registry_name="workforce_demo_v2",
        csv_path=SAMPLE_DATA_DIR / "workforce_demo_v2.csv",
        domain="Workforce",
        role="primary",
        sidebar_label="Workforce demo",
        app_dataset_name="workforce_demo",
    ),
    "workforce_demo": GoldenDataset(
        registry_name="workforce_demo",
        csv_path=SAMPLE_DATA_DIR / "workforce_demo.csv",
        domain="Workforce",
        role="legacy_smoke",
        sidebar_label=None,
        app_dataset_name="workforce_demo",
    ),
    "trend_volatility_test": GoldenDataset(
        registry_name="trend_volatility_test",
        csv_path=SAMPLE_DATA_DIR / "trend_volatility_test.csv",
        domain="Synthetic time series",
        role="secondary",
        sidebar_label=None,
        app_dataset_name="trend_volatility_test",
    ),
}


def _manufacturing_full_journey_sections() -> tuple[str, ...]:
    return (
        *STANDARD_RESULTS_SECTIONS,
        *FULL_EXECUTIVE_REASONING_SECTIONS,
        SECTION_SYSTEM_TRANSPARENCY,
    )


def _education_snapshot_journey_sections() -> tuple[str, ...]:
    return (
        SECTION_DIRECT_ANSWER,
        EXECUTIVE_REASONING_HEADING,
        SECTION_SYSTEM_TRANSPARENCY,
    )


def _workforce_clarification_journey_sections() -> tuple[str, ...]:
    return (EXECUTIVE_REASONING_HEADING,)


def _manufacturing_temporal_filter_journey_sections() -> tuple[str, ...]:
    return (SECTION_DIRECT_ANSWER, SECTION_SYSTEM_TRANSPARENCY)


def _manufacturing_snapshot_analysis_journey_sections() -> tuple[str, ...]:
    return (
        SECTION_DIRECT_ANSWER,
        EXECUTIVE_REASONING_HEADING,
        SECTION_SYSTEM_TRANSPARENCY,
    )


def _manufacturing_snapshot_contributors_journey_sections() -> tuple[str, ...]:
    return (SECTION_DIRECT_ANSWER, SECTION_SYSTEM_TRANSPARENCY)


CLARIFICATION_COMPLETE_SECTIONS: tuple[str, ...] = (
    SECTION_DIRECT_ANSWER,
    EXECUTIVE_REASONING_HEADING,
    SECTION_SYSTEM_TRANSPARENCY,
)


GOLDEN_SCENARIOS: dict[str, GoldenScenario] = {
    "manufacturing_bootstrap_smoke": GoldenScenario(
        scenario_id="manufacturing_bootstrap_smoke",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10c bootstrap smoke: load manufacturing sample, run a "
            "single-step question, and verify core report sections including "
            "executive reasoning."
        ),
        question=GoldenQuestion(
            question="Which production line has the highest defects and what is the risk?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=_manufacturing_full_journey_sections(),
            notes=(
                "Completes without clarification on the manufacturing golden CSV. "
                "Used for the first AppTest smoke while broader journeys are added "
                "in later milestones."
            ),
        ),
    ),
    "manufacturing_analysis_journey": GoldenScenario(
        scenario_id="manufacturing_analysis_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Manufacturing golden journey: broad analysis with metric and dimension "
            "clarification before a full executive report is rendered."
        ),
        question=GoldenQuestion(
            question="Analyse this dataset",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(
                ClarificationStep(clarification_type="metric", option="defects"),
                ClarificationStep(clarification_type="dimension", option="production_line"),
            ),
            visible_sections=_manufacturing_full_journey_sections(),
        ),
    ),
    "manufacturing_analyse_dataset": GoldenScenario(
        scenario_id="manufacturing_analyse_dataset",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description="Alias retained for registry compatibility.",
        question=GoldenQuestion(
            question="Analyse this dataset",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(
                ClarificationStep(clarification_type="metric", option="defects"),
                ClarificationStep(clarification_type="dimension", option="production_line"),
            ),
            visible_sections=_manufacturing_full_journey_sections(),
        ),
    ),
    "education_snapshot_journey": GoldenScenario(
        scenario_id="education_snapshot_journey",
        dataset=GOLDEN_DATASETS["education_demo"],
        description=(
            "Education golden journey: April snapshot question completes without "
            "clarification and activates snapshot transparency."
        ),
        question=GoldenQuestion(
            question="How has attendance changed in April 2026?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=_education_snapshot_journey_sections(),
            expects_snapshot=True,
        ),
    ),
    "workforce_clarification_journey": GoldenScenario(
        scenario_id="workforce_clarification_journey",
        dataset=GOLDEN_DATASETS["workforce_demo_v2"],
        description=(
            "Workforce golden journey: ambiguous performance question requires metric "
            "clarification before executive reasoning is shown."
        ),
        question=GoldenQuestion(
            question="How has performance changed?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(ClarificationStep(clarification_type="metric", option="hours"),),
            visible_sections=_workforce_clarification_journey_sections(),
        ),
    ),
    "education_metric_clarification_journey": GoldenScenario(
        scenario_id="education_metric_clarification_journey",
        dataset=GOLDEN_DATASETS["education_demo"],
        description=(
            "Milestone 10e: ambiguous performance question requires metric "
            "clarification before results are shown."
        ),
        question=GoldenQuestion(
            question="How has performance changed?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(
                ClarificationStep(clarification_type="metric", option="attendance_rate"),
            ),
            visible_sections=CLARIFICATION_COMPLETE_SECTIONS,
        ),
    ),
    "education_dimension_clarification_journey": GoldenScenario(
        scenario_id="education_dimension_clarification_journey",
        dataset=GOLDEN_DATASETS["education_demo"],
        description=(
            "Milestone 10e: causal question requires dimension clarification "
            "before analysis completes."
        ),
        question=GoldenQuestion(
            question="What caused attendance to drop?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="dimension",
            clarification_steps=(
                ClarificationStep(clarification_type="dimension", option="school"),
            ),
            visible_sections=CLARIFICATION_COMPLETE_SECTIONS,
        ),
    ),
    "workforce_clarification_recovery_journey": GoldenScenario(
        scenario_id="workforce_clarification_recovery_journey",
        dataset=GOLDEN_DATASETS["workforce_demo_v2"],
        description=(
            "Milestone 10e: resolve metric clarification, then run a second "
            "question without stale clarification UI."
        ),
        question=GoldenQuestion(
            question="How has performance changed?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(ClarificationStep(clarification_type="metric", option="hours"),),
        ),
        follow_up_question=GoldenQuestion(
            question="Which department has the highest hours?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=CLARIFICATION_COMPLETE_SECTIONS,
        ),
    ),
    "education_performance_clarification": GoldenScenario(
        scenario_id="education_performance_clarification",
        dataset=GOLDEN_DATASETS["education_demo"],
        description="Registry alias for education_metric_clarification_journey.",
        question=GoldenQuestion(
            question="How has performance changed?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(
                ClarificationStep(clarification_type="metric", option="attendance_rate"),
            ),
            visible_sections=CLARIFICATION_COMPLETE_SECTIONS,
        ),
    ),
    "workforce_analyse_dataset": GoldenScenario(
        scenario_id="workforce_analyse_dataset",
        dataset=GOLDEN_DATASETS["workforce_demo_v2"],
        description="Workforce broad analysis with metric clarification.",
        question=GoldenQuestion(
            question="Analyse this dataset",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            notes="Future workforce broad-analysis journey.",
        ),
    ),
    "manufacturing_temporal_filter_journey": GoldenScenario(
        scenario_id="manufacturing_temporal_filter_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10f: Q1 variance question applies a temporal filter and "
            "completes without snapshot mode."
        ),
        question=GoldenQuestion(
            question="Which production line has the highest defects in Q1 2026?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=_manufacturing_temporal_filter_journey_sections(),
            expects_temporal_filter=True,
        ),
    ),
    "manufacturing_snapshot_analysis_journey": GoldenScenario(
        scenario_id="manufacturing_snapshot_analysis_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10f: April snapshot question completes without clarification "
            "and activates snapshot transparency."
        ),
        question=GoldenQuestion(
            question="How has defects changed in April 2026?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=_manufacturing_snapshot_analysis_journey_sections(),
            expects_snapshot=True,
        ),
    ),
    "manufacturing_snapshot_contributors_journey": GoldenScenario(
        scenario_id="manufacturing_snapshot_contributors_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10f: April snapshot question with an explicit dimension "
            "surfaces snapshot contributor transparency."
        ),
        question=GoldenQuestion(
            question="How has defects changed in April 2026 by production line?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=_manufacturing_snapshot_contributors_journey_sections(),
            expects_snapshot=True,
            expects_snapshot_contributors=True,
        ),
    ),
    "dataset_onboarding_journey": GoldenScenario(
        scenario_id="dataset_onboarding_journey",
        dataset=GOLDEN_DATASETS["workforce_demo"],
        description=(
            "Milestone 10g: upload path loads a valid CSV, profiles it, and "
            "supports analysis."
        ),
        question=GoldenQuestion(
            question="Which department has the highest hours?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=(SECTION_DIRECT_ANSWER,),
        ),
    ),
    "dataset_replacement_journey": GoldenScenario(
        scenario_id="dataset_replacement_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10g: loading a second dataset clears stale analysis "
            "results and supports a new analysis."
        ),
        question=GoldenQuestion(
            question="Which production line has the highest defects?",
            expected_outcome=ExpectedOutcome.RESULTS,
        ),
        replacement_dataset=GOLDEN_DATASETS["education_demo"],
        replacement_question=GoldenQuestion(
            question="Which school has the highest behaviour incidents?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=(SECTION_DIRECT_ANSWER,),
        ),
    ),
    "dataset_invalid_recovery_journey": GoldenScenario(
        scenario_id="dataset_invalid_recovery_journey",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description=(
            "Milestone 10g: reject an empty upload while preserving the active "
            "dataset and recovery analysis."
        ),
        question=GoldenQuestion(
            question="Which production line has the highest defects?",
            expected_outcome=ExpectedOutcome.RESULTS,
            visible_sections=(SECTION_DIRECT_ANSWER,),
        ),
        invalid_fixture_path=SAMPLE_DATA_DIR / "fixtures" / "empty.csv",
        invalid_error_marker=INVALID_EMPTY_CSV_MARKER,
    ),
}


def get_scenario(scenario_id: str) -> GoldenScenario:
    """Return a registered golden scenario by id."""
    try:
        return GOLDEN_SCENARIOS[scenario_id]
    except KeyError as exc:
        raise KeyError(f"Unknown golden scenario: {scenario_id!r}") from exc
