"""Optional narrative generation for completed deterministic analysis."""

from __future__ import annotations

from ui.models import AnalysisResult
from ui.transparency import build_transparency_trail_lines

from src.operational_intelligence.llm.business_narrative_translation import (
    BusinessNarrativeTranslator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import NarrativeRuntimeConfig
from src.operational_intelligence.llm.narrative_generation import generate_narrative
from src.operational_intelligence.llm.narrative_models import (
    DeterministicAnalysisSnapshot,
    NarrativeResponse,
)
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder


def _finding_summary(title: str, description: str) -> str:
    return f"{title}: {description}"


def build_deterministic_analysis_snapshot(result: AnalysisResult) -> DeterministicAnalysisSnapshot:
    """Capture a read-only snapshot of deterministic analysis output."""
    report = result.report
    if report is None:
        raise ValueError("Cannot build narrative snapshot without an executive report.")

    analytical_findings = tuple(
        _finding_summary(finding.title, finding.description) for finding in result.findings
    )
    operational_assessment = None
    if report.operational_assessment is not None:
        assessment = report.operational_assessment
        operational_assessment = (
            f"{assessment.assessment_level}: {assessment.rationale}"
        )

    executive_conclusions = tuple(
        conclusion.headline for conclusion in report.executive_conclusions
    )
    priority_actions = tuple(action.action for action in report.priority_actions)

    reasoning_trace = tuple(
        f"Theme {theme.theme_id}: {theme.theme_label}" for theme in report.executive_themes
    )
    if report.operational_assessment is not None:
        reasoning_trace = reasoning_trace + (
            f"Assessment: {report.operational_assessment.rationale}",
        )
    reasoning_trace = BusinessNarrativeTranslator().translate_reasoning_trace(reasoning_trace)

    transparency_lines = build_transparency_trail_lines(
        temporal_filter=result.temporal_filter,
        snapshot_context=result.snapshot_context,
        findings=result.findings,
        request=result.request,
        routes=result.routes,
        metrics_analysed=result.metrics_analysed,
    )

    included_sections: list[str] = ["Direct Answer", "Executive Summary"]
    if analytical_findings:
        included_sections.append("Analytical Findings")
    if operational_assessment:
        included_sections.append("Operational Assessment")
    if executive_conclusions:
        included_sections.append("Executive Conclusions")
    if priority_actions:
        included_sections.append("Priority Actions")
    if transparency_lines:
        included_sections.append("System Transparency")

    return DeterministicAnalysisSnapshot(
        question=result.request.question,
        direct_answer=result.direct_answer,
        executive_summary=report.executive_summary,
        analytical_findings=analytical_findings,
        operational_assessment=operational_assessment,
        executive_conclusions=executive_conclusions,
        priority_actions=priority_actions,
        transparency_summary=tuple(transparency_lines),
        reasoning_trace=reasoning_trace,
        source_sections=tuple(included_sections),
    )


def maybe_generate_narrative(
    result: AnalysisResult,
    config: NarrativeRuntimeConfig | None = None,
) -> tuple[NarrativeResponse | None, tuple[str, ...]]:
    """Return optional narrative output without mutating deterministic analysis."""
    runtime_config = config or NarrativeRuntimeConfig.from_environment()
    if not runtime_config.enabled:
        return None, ()
    if result.clarification is not None or result.report is None:
        return None, ()

    snapshot = build_deterministic_analysis_snapshot(result)
    request = NarrativeRequestBuilder().build(snapshot)
    artifact = PromptArtifactBuilder().build(request)
    outcome = generate_narrative(artifact, runtime_config)
    return outcome.response, outcome.warnings
