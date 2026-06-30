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
| Completed | Implemented (Milestone 8.1) | Temporal Intelligence — Phase 1 (explicit periods) |
| Completed | Implemented (Milestone 7.2) | Adaptive Direct Answer Summarisation             |
| Completed | Implemented (Milestone 8.5) | Snapshot Intelligence                            |
| High      | Planned                     | Pipeline ↔ Transparency Contract Protection      |
| Medium    | Planned                     | Month-only Cross-Year Ambiguity                  |
| Medium    | Planned                     | Temporal Intent Without Applicable Date Columns  |
| Medium    | Planned                     | Unsupported Temporal Intent Transparency         |
| Low       | Planned                     | Temporal Filter Deduplication                    |
| Low       | Planned                     | Year-Only Temporal Parsing False Positives       |
| Medium    | Deferred                    | Capability-Aware Investigation Suggestions       |
| Medium    | Partially Implemented       | Metrics Analysed Presentation Improvements       |
| Low       | Planned                     | Empty-Findings Answer Does Not Reference Temporal Scope |
| Low       | Planned                     | Deterministic Answer Transparency Alignment      |
| Low       | Future Enhancement          | Auto-Resolved Decision Transparency Expansion    |
| Low       | Future Enhancement          | Contextual Baseline Intelligence                 |
| Future    | Future Enhancement          | Guided Drill-Down Investigations                 |
| Low       | Deferred (Milestone 13e)    | Presentation helper consolidation                |
| Low       | Deferred (Milestone 13e)    | Deprecated navigation placeholder removal        |
| Low       | Deferred (Milestone 13e)    | CSS token extraction across branding/results     |

---

# Temporal Intelligence — Phase 1 (Explicit Periods)

**Status:** Implemented (Milestone 8.1)

## What was implemented

Phase 1 temporal intelligence now supports deterministic parsing and pipeline-level filtering for:

* month + year (April 2026)
* month only (January)
* year only (2026)
* quarter + year (Q1 2026)

The pipeline applies temporal scope before analytical tool execution. System Transparency reports the applied period, date column, and record counts when filtering runs successfully.

## Remaining Phase 2+ scope

The following are intentionally deferred:

* relative periods (`this month`, `last month`)
* comparative periods (`April vs May`)
* temporal year clarification for month-only questions across multiple years
* temporal capability notices when filtering cannot be applied

See the dedicated entries below for known Phase 1 limitations.

Phase 1 should be considered functionally complete. Remaining Temporal Intelligence items represent capability expansion, user-experience improvements, or analytical trust enhancements rather than correctness defects.

---

# Snapshot Intelligence

**Status:** Implemented (Milestone 8.5)

## What was implemented

Snapshot Intelligence activates when temporal filtering reduces a dataset to a single period. Instead of misleading single-bucket trend analysis, the pipeline produces snapshot findings with baseline comparison, direct answers, and optional contributor transparency.

Capabilities include:

* Single-period detection after temporal filtering
* Snapshot direct answers with baseline comparison language
* Snapshot contributor analysis when a dimension resolves
* System Transparency trails for snapshot mode and contributors

Application behavioural coverage exists in Milestone 10f AppTests.

## Remaining scope

Future snapshot enhancements (cross-period comparison, richer contributor UX) remain deferred. See other Temporal Intelligence Phase 2+ entries below.

# Month-only Cross-Year Ambiguity

**Status:** Planned

## Context

Month-only questions such as "What happened in January?" are parsed without a year constraint.

### Current behaviour

When multiple years exist in the dataset, filtering matches all rows for that calendar month across years.

### Problem

The period label (e.g. "January") may imply a single month scope, but the analysis may span multiple years unless the user specifies a year.

### Desired future behaviour

When multiple years are present, prompt for year clarification before applying month-only filters.

## Suggested future milestone

**Milestone 8 — Temporal Intelligence (Phase 2+)**

---

# Year-Only Temporal Parsing False Positives

**Status:** Planned

## Context

Phase 1 temporal intelligence supports explicit year parsing.

### Example

> "What happened in 2026?"

## Problem

The current parser may interpret standalone year values as temporal constraints even when the year is not being used as a time reference.

Potential examples include:

* identifiers,
* codes,
* free-text descriptions,
* domain-specific labels.

While uncommon in current datasets, this may become more relevant as dataset diversity increases.

## Desired future behaviour

Improve temporal parsing confidence by incorporating additional contextual validation around year references.

## Suggested future milestone

**Milestone 8 — Temporal Intelligence Phase 2+**

---

# Temporal Intent Without Applicable Date Columns

**Status:** Planned

## Context

A user may ask a temporal question against a dataset that has no profiled date columns.

### Current behaviour

The pipeline cannot apply the requested temporal scope and returns generic no-findings output without temporal transparency metadata.

### Problem

The user asked for a specific period, but the system provides no clear explanation that temporal filtering could not be applied.

### Desired future behaviour

Provide a clear capability notice explaining that the dataset lacks a usable date column for the requested period.

## Suggested future milestone

**Milestone 8 — Temporal Intelligence (Phase 2+)**

---

# Unsupported Temporal Intent Transparency

**Status:** Planned

## Context

Users may ask questions containing temporal intent that is currently outside the supported Phase 1 capability set.

Examples include:

* compare April to May
* last month
* since March
* after April

## Current behaviour

Temporal parsing intentionally ignores unsupported temporal constructs and analytical execution proceeds without temporal filtering.

## Problem

Users may incorrectly assume that temporal filtering was applied when it was not.

## Desired future behaviour

Provide explicit transparency indicating:

* temporal intent was detected,
* the requested temporal construct is not currently supported,
* analysis proceeded without temporal filtering.

## Suggested future milestone

**Milestone 8 — Temporal Intelligence Phase 2**

---

# Empty-Findings Answer Does Not Reference Temporal Scope

**Status:** Planned

## Context

When a temporal filter produces zero matching records, System Transparency can show `Records analysed: 0 of N`, but the Direct Answer layer may still report a generic message.

### Current behaviour

> "No findings were identified from the analysis."

### Problem

The answer does not explain that zero records matched the requested period, which can feel inconsistent with the transparency panel.

### Desired future behaviour

Reference temporal scope in answer generation when a filter was applied and zero records remain (or when zero findings result from an empty filtered scope).

## Suggested future milestone

**Milestone 8 — Temporal Intelligence (Phase 2+)**

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

# Temporal Filter Deduplication

**Status:** Planned

## Context

Milestone 8.1 introduced temporal filtering and temporal transparency.

During review, it was identified that temporal filtering logic may be executed in multiple locations when constructing both:

* the filtered analytical dataset,
* the temporal transparency metadata.

## Problem

If temporal filtering logic evolves independently in different code paths, transparency metadata could drift from the actual dataset analysed.

Examples include:

* filtered row counts,
* temporal scope boundaries,
* invalid date handling.

This would undermine user trust because System Transparency may no longer accurately describe analytical execution.

## Desired future behaviour

Temporal filtering should be applied once and reused by:

* analytical execution,
* temporal transparency reporting.

This guarantees a single source of truth for temporal scope.

## Suggested future milestone

**Milestone 8 — Temporal Intelligence Hardening**

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


# Dimension Synonym Resolution

**Status:** Future Enhancement

Users may refer to dataset dimensions using natural business language that does not directly match column names.

Example:

> "by class"

In the education dataset, the closest available dimension is `year_level`, but the system does not currently map `class` to `year_level`.

Future behaviour should support controlled synonym mapping or clarification when a user refers to an unmapped dimension.

---

# Presentation Layer — Post-MVP Consolidation

**Status:** Deferred (Milestone 13e)

Milestone 13e established a lightweight design system without deep refactors. The following remain acceptable post-MVP cleanup:

* Consolidate `DEFAULT_INVESTIGATION_LIMIT` and `DEFAULT_VISIBLE_ACTION_LIMIT` in `ui/results_headings.py`
* Remove deprecated [`ui/components/results_navigation_placeholder.py`](ui/components/results_navigation_placeholder.py) once test references are migrated
* Extract shared CSS tokens if branding and results styles continue to diverge
* Consolidate duplicate overview bullet formatting helpers if Analysis Overview is reintroduced elsewhere