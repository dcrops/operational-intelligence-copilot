"""Optional narrative generation for completed deterministic analysis."""

from __future__ import annotations

from ui.models import AnalysisResult
from ui.transparency import (
    format_auto_resolved_trail,
    format_clarification_trail,
    format_metrics_analysed_trail,
    format_snapshot_contributors_trail,
    format_snapshot_trail,
    format_temporal_filter_trail,
)

from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import is_narrative_enabled
from src.operational_intelligence.llm.narrative_factory import resolve_narrative_generator
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

    transparency_lines: list[str] = []
    transparency_lines.extend(format_temporal_filter_trail(result.temporal_filter))
    transparency_lines.extend(format_snapshot_trail(result.snapshot_context))
    transparency_lines.extend(format_snapshot_contributors_trail(result.findings))
    transparency_lines.extend(format_clarification_trail(result.request))
    transparency_lines.extend(
        format_auto_resolved_trail(
            result.request,
            result.findings,
            result.routes,
            metrics_analysed=result.metrics_analysed,
        )
    )
    transparency_lines.extend(format_metrics_analysed_trail(result.metrics_analysed))

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


def maybe_generate_narrative(result: AnalysisResult) -> NarrativeResponse | None:
    """Return optional narrative output without mutating deterministic analysis."""
    if not is_narrative_enabled():
        return None
    if result.clarification is not None or result.report is None:
        return None

    snapshot = build_deterministic_analysis_snapshot(result)
    request = NarrativeRequestBuilder().build(snapshot)
    artifact = PromptArtifactBuilder().build(request)
    return resolve_narrative_generator().generate(artifact)
