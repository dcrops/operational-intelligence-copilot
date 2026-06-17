# Technical Debt Log

Tracked limitations, known gaps, consciously deferred enhancements, and planned future capabilities for the Operational Intelligence Copilot.

---

## What belongs here?

Items in this document are:

* known limitations,
* consciously deferred enhancements,
* architectural improvements,
* future capabilities identified during testing.

This document is intended to prevent scope creep while preserving valuable insights discovered throughout development.

Items recorded here are not necessarily defects. Many represent deliberate trade-offs made to maintain delivery momentum and milestone focus.

---

## Prioritisation

| Priority  | Status                      | Item                                             |
| --------- | --------------------------- | ------------------------------------------------ |
| Completed | Implemented (Milestone 7.2) | Adaptive Direct Answer Summarisation             |
| High      | Planned                     | Pipeline ↔ Transparency Contract Protection      |
| Medium    | Planned                     | Temporal Intelligence / Date Constraint Handling |
| Medium    | Deferred                    | Capability-Aware Investigation Suggestions       |
| Medium    | Partially Implemented       | Metrics Analysed Presentation Improvements       |
| Low       | Planned                     | Deterministic Answer Transparency Alignment      |
| Low       | Future Enhancement          | Auto-Resolved Decision Transparency Expansion    |
| Low       | Future Enhancement          | Contextual Baseline Intelligence                 |
| Future    | Future Enhancement          | Guided Drill-Down Investigations                 |

---

# Temporal Intelligence / Date Constraint Handling

**Status:** Planned

## Context

Manual testing identified that questions containing date or period constraints are currently analysed across the full dataset.

**Example question:**

> "How has performance changed for April 2026?"

### Current behaviour

The system analyses the full available dataset (e.g. January to June 2026).

### Problem

The user asked for a specific period, but temporal constraints are not currently extracted or applied.

This can produce misleading answers.

## Desired future behaviour

The system should detect temporal constraints in user questions and either:

* filter the dataset before analysis, or
* explicitly warn that temporal filtering is not yet supported.

## Examples to support in future

* April 2026
* March
* Q1 2026
* Q2
* this month
* last month
* compare April to May
* since March
* after April

## Suggested future milestone

**Milestone 8 — Temporal Intelligence**

### Potential phased approach

| Phase   | Scope                            |
| ------- | -------------------------------- |
| Phase 1 | Explicit months, years, quarters |
| Phase 2 | Relative periods                 |
| Phase 3 | Comparative periods              |

---

# Capability-Aware Investigation Suggestions

**Status:** Deferred

## Context

Milestone 7 introduced deterministic investigation suggestions intended to guide users toward sensible analytical next steps.

During testing, it became apparent that some suggested investigations could not always be executed through the current analytical capabilities.

### Example flow

Question:

> "How has attendance changed over time?"

Suggested investigation:

> "Review which groups contributed most to the observed change."

User asks:

> "Which schools contributed most?"

Current behaviour:

> No findings identified.

## Problem

The investigation suggestion generator currently produces plausible analytical next steps without verifying that those next steps can be:

* routed successfully,
* resolved unambiguously,
* executed using existing analytical tools.

This exposes capability boundaries within the current platform.

## Desired future behaviour

Suggested investigations should only be surfaced when they map to analyses that the current platform can reliably perform.

Potential future capabilities include:

* capability-aware suggestion generation,
* executable follow-up investigations,
* guided drill-down workflows.

## Suggested future milestone

**Milestone 7.5 — Capability-Aware Investigation Suggestions**

---

# Adaptive Direct Answer Summarisation

**Status:** Implemented (Milestone 7.2)

## Context

Early anomaly direct answers summarised findings using only anomaly counts and the most extreme value.

### Previous example

> "5 unusual HIGH values were detected for defects. The most extreme value was 79."

User testing demonstrated that this often forced users to inspect supporting evidence even when only a small number of anomalies existed.

## What was implemented

Milestone 7.2 introduced adaptive direct-answer behaviour for anomaly findings.

| Anomaly Count | Behaviour                                      |
| ------------- | ---------------------------------------------- |
| 1–5           | Show all anomalous records                     |
| 6–20          | Show representative examples plus summary      |
| >20           | Show summary only and direct users to evidence |

The milestone also introduced contextual anomaly explanations.

Examples include:

> "Row 126: defects = 52, compared with an average of 8.22 (z-score 5.08)."

This preserved statistical transparency while improving interpretability for non-technical users.

## Notes

Future enhancements may include:

* contextual baselines,
* audience-aware explanations,
* executive versus analyst presentation modes.

---

# Pipeline ↔ Transparency Contract Protection

**Status:** Planned

## Context

The logic used to determine "Metrics analysed" currently exists independently within:

* pipeline anomaly resolution,
* transparency rendering.

## Problem

Future changes could cause the pipeline and transparency layers to drift, resulting in contradictory outputs.

## Desired future behaviour

Introduce contract tests or shared helper logic to guarantee alignment between analytical execution and transparency reporting.

## Potential approaches

* shared helper extraction,
* pipeline versus transparency contract tests.

---

# Deterministic Answer Transparency Alignment

**Status:** Planned

## Context

Transparency information currently appears only within the user interface.

Examples include:

* clarification history,
* inferred analytical decisions,
* metrics analysed.

## Problem

Exported or copied deterministic answers do not include the same transparency context visible within the interface.

## Desired future behaviour

Allow deterministic answers and future report exports to optionally include transparency metadata.

## Suggested future milestone

**Milestone 9 — Audit and Export Enhancements**

---

# Metrics Analysed Presentation Improvements

**Status:** Partially Implemented

## Current state

Milestone 7.1 introduced a dedicated "Metrics analysed" section within System Transparency.

However, users may still interpret all listed metrics as producing findings.

Further UX improvements remain planned.

## Context

The System Transparency section lists all metrics scanned during anomaly analysis.

## Problem

Users may interpret this as indicating that all listed metrics produced findings.

### Example

Metrics analysed:

* defects
* downtime_minutes
* units_produced

Users may reasonably assume that all three metrics generated findings.

## Desired future behaviour

Clarify that:

> "All listed metrics were scanned. Findings appear only where issues were detected."

This improves interpretability without changing analytical behaviour.

---

# Auto-Resolved Decision Transparency Expansion

**Status:** Future Enhancement

## Context

Milestone 7.1 introduced transparency around automatically inferred analytical decisions.

Current examples include:

* aggregation,
* comparison direction.

## Desired future behaviour

Expand transparency to include additional inferred decisions where appropriate.

Potential examples include:

* date grain selection,
* default grouping behaviour,
* automatically selected metrics,
* automatically selected dimensions.

## Notes

These should only be displayed when genuinely inferred and supported by deterministic logic.

---

# Contextual Baseline Intelligence

**Status:** Future Enhancement

## Context

Current anomaly explanations compare anomalous values against overall dataset averages.

Example:

> "Row 126: defects = 52, compared with an average of 8.22."

While statistically valid, the average currently represents the same population used to calculate z-scores rather than a context-specific peer group.

## Problem

Users may naturally interpret the comparison as representing:

* the same school,
* the same department,
* the same production line,
* the same time period.

However, the current implementation uses global dataset baselines.

This can limit interpretability for more sophisticated analytical scenarios.

## Desired future behaviour

Support contextual anomaly baselines where appropriate.

Examples may include comparisons against:

* the same dimension group,
* the same department,
* the same school,
* the same production line,
* the same time period.

### Example

Current:

> "Line 2: defects = 52, compared with an average of 8.22."

Potential future behaviour:

> "Line 2: defects = 52, compared with the typical Line 2 value of 11."

## Potential future milestone

**Milestone 9+ — Context-Aware Anomaly Detection**

## Notes

The current implementation remains statistically correct and aligned with z-score calculations.

This enhancement would improve explanatory power rather than analytical correctness.

---

# Guided Drill-Down Investigations

**Status:** Future Enhancement

## Context

Current investigation suggestions are informational only.

Users must manually formulate new questions.

## Desired future behaviour

Allow investigation suggestions to trigger pre-configured analytical workflows automatically.

### Example

Attendance decreased by 3.2%.

Suggested investigation:

> [Which school contributed most?]

Selecting the investigation could automatically execute an appropriate analytical workflow without requiring the user to formulate a new question.

## Potential future capabilities

* tool chaining,
* investigation workflows,
* investigation state tracking,
* evidence propagation across investigations.

## Suggested future milestone

**Milestone 9 — Guided Drill-Down Investigations**


Snapshot Intelligence

Single-period temporal trend questions may produce
stable 0% trends because TrendAnalysisTool expects
multiple periods.

Future capability:
snapshot-oriented analytical reasoning.