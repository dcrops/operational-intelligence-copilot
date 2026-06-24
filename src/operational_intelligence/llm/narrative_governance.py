"""Vendor-neutral governance rules for prompt artifact construction."""

from __future__ import annotations

PROMPT_ARTIFACT_VERSION = "1.0"

OBJECTIVE_EXECUTIVE_NARRATIVE = "executive_narrative"
OBJECTIVE_EXECUTIVE_SUMMARY = "executive_summary"
DEFAULT_NARRATIVE_OBJECTIVE = OBJECTIVE_EXECUTIVE_NARRATIVE

SUPPORTED_NARRATIVE_OBJECTIVES = frozenset(
    {
        OBJECTIVE_EXECUTIVE_NARRATIVE,
        OBJECTIVE_EXECUTIVE_SUMMARY,
    }
)

SECTION_DIRECT_ANSWER = "Direct Answer"
SECTION_EXECUTIVE_SUMMARY = "Executive Summary"
SECTION_ANALYTICAL_FINDINGS = "Analytical Findings"
SECTION_OPERATIONAL_ASSESSMENT = "Operational Assessment"
SECTION_EXECUTIVE_CONCLUSIONS = "Executive Conclusions"
SECTION_PRIORITY_ACTIONS = "Priority Actions"
SECTION_SYSTEM_TRANSPARENCY = "System Transparency"

PROHIBITED_BEHAVIOURS = (
    "calculate_metrics",
    "infer_causation",
    "change_risk_level",
    "introduce_new_findings",
    "override_direct_answer",
)

SYSTEM_INSTRUCTIONS = (
    "Use only the evidence references and verbatim deterministic sections provided.",
    "Do not calculate metrics or perform additional analysis.",
    "Do not infer causation beyond stated evidence.",
    "Do not change risk levels or operational assessment.",
    "Do not introduce findings not present in evidence references.",
    "If evidence is insufficient, state the limitation explicitly.",
)

OBJECTIVE_INSTRUCTIONS: dict[str, tuple[str, ...]] = {
    OBJECTIVE_EXECUTIVE_NARRATIVE: (
        "Produce a concise executive narrative grounded in the supplied evidence.",
    ),
    OBJECTIVE_EXECUTIVE_SUMMARY: (
        "Produce a concise executive summary grounded in the supplied evidence.",
    ),
}
