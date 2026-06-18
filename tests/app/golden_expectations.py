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
SECTION_RESULTS = "Results"

STANDARD_RESULTS_SECTIONS: tuple[str, ...] = (
    SECTION_DIRECT_ANSWER,
    ANALYSIS_OVERVIEW_HEADING,
    ANALYTICAL_FINDINGS_HEADING,
)

EXECUTIVE_REASONING_SECTIONS: tuple[str, ...] = (
    EXECUTIVE_REASONING_HEADING,
    SECTION_OPERATIONAL_ASSESSMENT,
)


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
    notes: str = ""


@dataclass(frozen=True)
class GoldenScenario:
    """Dataset + question pairing for AppTest and future Playwright journeys."""

    scenario_id: str
    dataset: GoldenDataset
    question: GoldenQuestion
    description: str = ""


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


def _manufacturing_executive_sections() -> tuple[str, ...]:
    return (
        *STANDARD_RESULTS_SECTIONS,
        *EXECUTIVE_REASONING_SECTIONS,
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
            visible_sections=_manufacturing_executive_sections(),
            notes=(
                "Completes without clarification on the manufacturing golden CSV. "
                "Used for the first AppTest smoke while broader journeys are added "
                "in later milestones."
            ),
        ),
    ),
    "manufacturing_analyse_dataset": GoldenScenario(
        scenario_id="manufacturing_analyse_dataset",
        dataset=GOLDEN_DATASETS["manufacturing_demo"],
        description="Broad analysis question requiring clarification before results.",
        question=GoldenQuestion(
            question="Analyse this dataset",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            clarification_steps=(
                ClarificationStep(clarification_type="metric", option="defects"),
                ClarificationStep(clarification_type="dimension", option="production_line"),
            ),
            visible_sections=_manufacturing_executive_sections(),
            notes="Future Milestone 10e clarification journey.",
        ),
    ),
    "education_performance_clarification": GoldenScenario(
        scenario_id="education_performance_clarification",
        dataset=GOLDEN_DATASETS["education_demo"],
        description="Ambiguous performance question requires metric clarification.",
        question=GoldenQuestion(
            question="How has performance changed?",
            expected_outcome=ExpectedOutcome.CLARIFICATION,
            clarification_type="metric",
            notes="Future Milestone 10e education clarification journey.",
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
            notes="Future Milestone 10d/10e workforce journey.",
        ),
    ),
}


def get_scenario(scenario_id: str) -> GoldenScenario:
    """Return a registered golden scenario by id."""
    try:
        return GOLDEN_SCENARIOS[scenario_id]
    except KeyError as exc:
        raise KeyError(f"Unknown golden scenario: {scenario_id!r}") from exc
