"""Vendor-neutral governance rules for prompt artifact construction."""

from __future__ import annotations

PROMPT_ARTIFACT_VERSION = "1.2"

OBJECTIVE_EXECUTIVE_NARRATIVE = "executive_narrative"
OBJECTIVE_EXECUTIVE_SUMMARY = "executive_summary"
OBJECTIVE_EXECUTIVE_ADVISOR = "executive_advisor"
DEFAULT_NARRATIVE_OBJECTIVE = OBJECTIVE_EXECUTIVE_ADVISOR

SUPPORTED_NARRATIVE_OBJECTIVES = frozenset(
    {
        OBJECTIVE_EXECUTIVE_NARRATIVE,
        OBJECTIVE_EXECUTIVE_SUMMARY,
        OBJECTIVE_EXECUTIVE_ADVISOR,
    }
)

SECTION_DIRECT_ANSWER = "Direct Answer"
SECTION_EXECUTIVE_SUMMARY = "Executive Summary"
SECTION_ANALYTICAL_FINDINGS = "Analytical Findings"
SECTION_OPERATIONAL_ASSESSMENT = "Operational Assessment"
SECTION_EXECUTIVE_CONCLUSIONS = "Executive Conclusions"
SECTION_PRIORITY_ACTIONS = "Priority Actions"
SECTION_SYSTEM_TRANSPARENCY = "System Transparency"

ADVISOR_SECTION_KEY_MESSAGE = "Key Message"
ADVISOR_SECTION_WHY_THIS_MATTERS = "Why This Matters"
ADVISOR_SECTION_WHERE_TO_INVESTIGATE = "Where To Investigate First"
ADVISOR_SECTION_POSSIBLE_EXPLANATIONS = "Possible Explanations To Check"
ADVISOR_SECTION_EXECUTIVE_ACTIONS = "Executive Actions"
ADVISOR_SECTION_OPERATIONAL_INVESTIGATION = "Operational Investigation"

ADVISOR_SECTION_TITLES = (
    ADVISOR_SECTION_KEY_MESSAGE,
    ADVISOR_SECTION_WHY_THIS_MATTERS,
    ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
    ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
    ADVISOR_SECTION_EXECUTIVE_ACTIONS,
    ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
)

ADVISOR_SECTION_LABEL_KEY_MESSAGE = "KEY MESSAGE:"
ADVISOR_SECTION_LABEL_WHY_THIS_MATTERS = "WHY THIS MATTERS:"
ADVISOR_SECTION_LABEL_WHERE_TO_INVESTIGATE = "WHERE TO INVESTIGATE FIRST:"
ADVISOR_SECTION_LABEL_POSSIBLE_EXPLANATIONS = "POSSIBLE EXPLANATIONS TO CHECK:"
ADVISOR_SECTION_LABEL_EXECUTIVE_ACTIONS = "EXECUTIVE ACTIONS:"
ADVISOR_SECTION_LABEL_OPERATIONAL_INVESTIGATION = "OPERATIONAL INVESTIGATION:"
ADVISOR_SECTION_LABEL_LIMITATIONS = "LIMITATIONS:"

ADVISOR_SECTION_LABELS = (
    ADVISOR_SECTION_LABEL_KEY_MESSAGE,
    ADVISOR_SECTION_LABEL_WHY_THIS_MATTERS,
    ADVISOR_SECTION_LABEL_WHERE_TO_INVESTIGATE,
    ADVISOR_SECTION_LABEL_POSSIBLE_EXPLANATIONS,
    ADVISOR_SECTION_LABEL_EXECUTIVE_ACTIONS,
    ADVISOR_SECTION_LABEL_OPERATIONAL_INVESTIGATION,
    ADVISOR_SECTION_LABEL_LIMITATIONS,
)

ADVISOR_SECTION_LABEL_TO_TITLE = {
    ADVISOR_SECTION_LABEL_KEY_MESSAGE: ADVISOR_SECTION_KEY_MESSAGE,
    ADVISOR_SECTION_LABEL_WHY_THIS_MATTERS: ADVISOR_SECTION_WHY_THIS_MATTERS,
    ADVISOR_SECTION_LABEL_WHERE_TO_INVESTIGATE: ADVISOR_SECTION_WHERE_TO_INVESTIGATE,
    ADVISOR_SECTION_LABEL_POSSIBLE_EXPLANATIONS: ADVISOR_SECTION_POSSIBLE_EXPLANATIONS,
    ADVISOR_SECTION_LABEL_EXECUTIVE_ACTIONS: ADVISOR_SECTION_EXECUTIVE_ACTIONS,
    ADVISOR_SECTION_LABEL_OPERATIONAL_INVESTIGATION: ADVISOR_SECTION_OPERATIONAL_INVESTIGATION,
}

PROHIBITED_BEHAVIOURS = (
    "calculate_metrics",
    "infer_causation",
    "confirm_unsupported_causes",
    "change_risk_level",
    "introduce_new_findings",
    "override_direct_answer",
    "use_statistical_jargon_in_advisor_text",
)

SYSTEM_INSTRUCTIONS = (
    "Use only the evidence references and verbatim deterministic sections provided.",
    "Do not calculate metrics or perform additional analysis.",
    "Do not infer causation beyond stated evidence.",
    "Do not confirm unsupported causes; present possible explanations as hypotheses only.",
    "Do not change risk levels or operational assessment.",
    "Do not introduce findings not present in evidence references.",
    "If evidence is insufficient, state the limitation explicitly.",
    "Communicate to operational executives using plain business language.",
    "Avoid statistical jargon in advisor narrative text (for example z-score, standard deviation, anomaly threshold).",
    "Translate technical findings into natural executive language while preserving deterministic facts.",
    "State observed facts confidently; label possible explanations as hypotheses.",
    "Ground all recommendations in deterministic evidence.",
    "Reference dataset dimensions in investigation guidance only when they appear in the supplied evidence.",
)

OBJECTIVE_INSTRUCTIONS: dict[str, tuple[str, ...]] = {
    OBJECTIVE_EXECUTIVE_NARRATIVE: (
        "Produce a concise executive narrative grounded in the supplied evidence.",
    ),
    OBJECTIVE_EXECUTIVE_SUMMARY: (
        "Produce a concise executive summary grounded in the supplied evidence.",
    ),
    OBJECTIVE_EXECUTIVE_ADVISOR: (
        "Act as an executive advisor, not a summariser.",
        "Answer why the findings matter, where to investigate first, what explanations to check, and what practical next steps to take.",
        "Use the ordered advisor sections requested in the response format.",
        "Reference available dataset dimensions (such as school, department, campus, production line, region, month, or year level) in investigation and next-step guidance when they appear in evidence.",
        "Do not invent dimensions or facts beyond the closed-world evidence.",
    ),
}
