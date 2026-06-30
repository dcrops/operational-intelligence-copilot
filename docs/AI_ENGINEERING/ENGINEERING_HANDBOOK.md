# Operational Intelligence Copilot
# Engineering Handbook

**Version:** 1.0  
**Last Updated:** June 2026  
**Project Status:** Phase 4 — Presentation polish (Milestone 12d complete)  
**Current Milestone:** Phase 4 — Milestone 12d — Executive Narrative UX Refinement

---

# Purpose

This handbook is the primary engineering reference for the Operational Intelligence Copilot project.

It is intended to onboard both human engineers and AI assistants to the project without requiring historical chat conversations.

This document describes:

- The purpose of the project
- Engineering philosophy
- Development workflow
- AI collaboration model
- Coding standards
- Review standards
- Testing philosophy
- Current project status
- Future direction

This document should be considered the authoritative engineering guide for the repository.

---

# Project Overview

The Operational Intelligence Copilot is a domain-agnostic AI analytics platform designed to analyse structured operational datasets and produce explainable, evidence-backed executive reports.

Unlike traditional dashboards, the system combines deterministic analytical tools with structured executive reasoning to produce insights suitable for operational decision support.

The project exists primarily as an AI Engineering portfolio project and is intended to demonstrate production-quality engineering practices rather than simply AI capability.

---

# Project Objectives

The project aims to demonstrate:

- AI Engineering
- Clean Architecture
- Explainable AI
- Deterministic Reasoning
- Executive Reporting
- Automated Testing
- Engineering Documentation
- Production-quality Software Engineering

---

# Engineering Philosophy

The following principles guide every engineering decision.

## Deterministic Before Probabilistic

Where possible:

- analytics remain deterministic
- evidence remains deterministic
- reasoning remains deterministic

Large Language Models are intended to enhance the system in later milestones rather than replace deterministic reasoning.

---

## Evidence Before Conclusions

The analytical tools generate evidence.

The reasoning layer interprets evidence.

The presentation layer communicates reasoning.

Responsibilities should remain separated.

---

## Infrastructure Before Features

Reusable infrastructure should always be built before feature-specific implementations.

Examples include:

- Executive Reasoning Engine
- Snapshot Intelligence
- Application Testing Framework
- Golden Dataset Registry

---

## Reuse Before Duplication

Existing components should be reused wherever practical.

Before introducing new code:

- search for existing helpers
- refactor common behaviour
- avoid duplicate implementations

---

## Small Milestones

Large features should be broken into small milestones.

Each milestone should:

- have a single responsibility
- be independently testable
- be independently reviewable
- be independently committable

---

## Architecture Before Implementation

Architecture should always be discussed before implementation.

Implementation should never drive architecture.

---

## Explainability Over Cleverness

A simpler system with transparent reasoning is preferred over a more complex system whose behaviour cannot be explained.

---

## Maintainability Over Short-term Speed

Readable, maintainable code is preferred over clever implementations.

Future contributors should be able to understand the system without reverse engineering it.

---

# AI Collaboration Model

This project is intentionally developed using AI-assisted software engineering.

Different tools have different responsibilities.

## ChatGPT

Used primarily for:

- architecture
- engineering reviews
- roadmap planning
- milestone design
- trade-off analysis
- documentation
- code review
- testing strategy

ChatGPT acts as a senior AI engineering reviewer rather than a code generator.

---

## Cursor

Cursor is used for implementation.

### PLAN Mode

Used for:

- implementation planning
- architectural validation
- implementation review before coding

### AGENT Mode

Used for:

- implementation
- refactoring
- test creation
- documentation updates

Agent mode is generally limited to a single milestone.

---

## Human Responsibilities

The human engineer remains responsible for:

- engineering decisions
- architecture approval
- testing
- code review
- learning
- Git commits
- product direction

AI assists engineering.

It does not replace engineering judgement.

---

# Standard Development Workflow

Every milestone follows the same workflow.

```
Idea

↓

Architecture Discussion

↓

Milestone Definition

↓

Cursor PLAN Mode

↓

Review

↓

Cursor AGENT Mode

↓

Implementation Review

↓

Testing

↓

Architecture Review

↓

Git Commit

↓

Next Milestone
```

Large milestones should always be divided into smaller reviewable components.

---

# Review Philosophy

Every milestone is reviewed before being accepted.

Reviews consider:

- architecture
- maintainability
- readability
- reuse
- testing
- future extensibility

The objective is not simply to determine whether the code works.

The objective is to determine whether it is good engineering.

Constructive criticism is encouraged.

Agreement should follow evidence rather than preference.

---

# Testing Philosophy

Testing is considered part of engineering rather than a separate activity.

The project currently contains:

- Unit Tests
- Integration Tests
- Streamlit Application Tests
- Golden Datasets
- Golden User Journeys

Tests should verify behaviour rather than implementation wherever practical.

Avoid brittle assertions such as exact rendered wording.

Prefer behavioural assertions such as:

- clarification requested
- report generated
- executive reasoning rendered
- transparency rendered

---

# Documentation Philosophy

Documentation is considered part of the software.

Engineering documentation should evolve alongside the codebase.

Documentation should support:

- human engineers
- AI assistants
- future contributors

Major engineering decisions should be documented.

---

# Learning Philosophy

This project is intentionally treated as an AI Engineering apprenticeship.

The objective is understanding rather than speed.

Architectural discussions are considered valuable.

Trade-offs should be explored.

Engineering decisions should be explained.

---

# Current Project Status

Phase 1 (Deterministic Analytics), Phase 2 (Executive Reasoning), and Phase 3 (Application Quality Engineering) are complete.

Completed in Phase 3:

- Application Testing Framework (Milestone 10c)
- Golden User Journeys (Milestone 10d)
- Clarification Workflow Testing (Milestone 10e)
- Temporal & Snapshot Testing (Milestone 10f)
- Dataset Lifecycle Testing (Milestone 10g)
- Engineering Readiness & Regression (Milestone 10h)
- Golden Dataset Registry (Milestone 10b)
- Executive Reasoning Experience (Milestone 10a)

The deterministic platform is **engineering-ready** for Phase 4.

Phase 4 principle: **deterministic platform owns truth; AI layer owns communication.**

Completed in Phase 4 (Milestone 11a):

- AI narrative integration boundary under `src/operational_intelligence/llm/`
- Frozen `NarrativeRequest` / `NarrativeResponse` contract
- `DeterministicNarrativeGenerator` placeholder (no LLM calls)
- `OIC_NARRATIVE_ENABLED` feature flag (default off)
- Boundary tests in `tests/test_narrative_boundary.py`

Completed in Phase 4 (Milestone 11b):

- `PromptArtifact` vendor-neutral AI-ready evidence package
- `PromptArtifactBuilder` with structured `EvidenceReference` assembly
- `GroundingConstraints` with closed-world evidence contract
- Evidence → Artifact → Generator flow in `ui/narrative_service.py`
- Prompt construction tests in `tests/test_prompt_construction.py`

Completed in Phase 4 (Milestone 11c):

- `OpenAINarrativeGenerator` as first production LLM adapter
- Provider architecture via `OIC_NARRATIVE_PROVIDER` (`deterministic` | `openai`)
- `FallbackNarrativeGenerator` for resilient deterministic fallback
- `narrative_factory.py` — single provider resolution point
- OpenAI tests with fake `LLMClient` only (no real API calls in CI)

Completed in Phase 4 (Milestone 11d):

- Executive narrative section in results panel (renamed **Executive Summary** in Milestone 12d)
- Pure presentation helpers in `ui/narrative_presentation.py`
- Governance caption when narrative renders; placeholder when narrative is absent for non-UI disabled callers
- Deterministic sections remain primary and unchanged
- Deterministic narrative generator produces polished executive prose as a graceful fallback when AI-assisted communication is unavailable

Completed in Phase 4 (Milestone 11e):

- **AI Executive Advisor** — narrative evolves from summarisation to executive communication and investigation guidance
- Reusable `NarrativeSection` model; `NarrativeResponse.sections` replaces fixed advisor field names
- Ordered advisor sections: Key Message, Why This Matters, Where To Investigate First, Possible Explanations To Check, Executive Actions, Operational Investigation
- Prompt artifact version 1.2 with executive-advisor governance, plain-language rules, and dimension-aware investigation guidance
- **Executive Context Builder** — assembles structured executive context from translated artefacts for narrative generation
- `ExecutiveContext` model; narrative generators consume executive context rather than raw analytical telemetry
- UI iterates `NarrativeSection` objects dynamically; deterministic analytics remain authoritative
- Tests in `tests/test_executive_advisor_narrative.py` and `tests/test_executive_context_builder.py`

---

## Milestone 11f — Business Narrative Translation Layer

### Problem solved

Executive narratives previously exposed analytical implementation details intended for System Transparency — for example routing metadata (`Metric selected`, `Aggregation inferred`), internal tool names, snake_case field identifiers, and person-identifying record values.

### Solution

Introduced a reusable **Business Narrative Translation Layer** (`business_narrative_translation.py`) between Executive Reasoning and Executive Narrative generation. The layer classifies every analytical artefact into Preserve, Translate, Remove, or Abstract categories via a data-driven `TranslationRegistry`.

### Benefits

* Clean separation of concerns between analytical reasoning and executive presentation
* Reusable translation registry — extend terminology without scattered conditionals
* Audience-specific presentation from the same deterministic evidence
* Deterministic behaviour preserved throughout translation
* Improved executive readability
* Future domain extensibility via registry entries

### Engineering decisions

* **Registry-driven translation** — rules defined as data in `TranslationRegistry`, not embedded in builders
* **Presentation-only transformation** — analytics, routing, Executive Reasoning, and System Transparency unchanged
* **Preserved traceability** — `translate_identifier_with_source()` retains source identifiers alongside display labels
* **Deterministic ordering retained** — translation never reorders metrics, dimensions, or investigation targets
* **Compatibility layer** — `executive_language.py` delegates to `BusinessNarrativeTranslator` without breaking existing imports
* **Three translation boundaries** — snapshot (`narrative_service.py`), context (`ExecutiveContextBuilder`), and OpenAI output post-processing

### Testing

Unit tests per category in `tests/test_business_narrative_translation.py`:

* **Preserve** — business metrics and operational entities unchanged
* **Translate** — known identifier and prose mappings
* **Remove** — transparency and routing metadata filtered
* **Abstract** — person-identifying values abstracted for person dimensions only

Integration leak tests in `tests/test_executive_context_builder.py` assert Executive Narrative context excludes internal terminology.

End-to-end ordered-concepts regression validates Preserve, Translate, Remove, and Abstract together.

Manual validation confirms Executive Narrative output is executive-safe (no routing metadata, no raw person names in person-dimension analyses).

### Milestone summary (portfolio)

Milestone 11f introduced a Business Narrative Translation Layer that cleanly separates deterministic analytical reasoning from executive communication. By introducing a reusable, registry-driven translation architecture, the system now presents the same underlying evidence differently depending on audience, improving executive readability while preserving transparency, determinism, and traceability.

Completed in Phase 4 (Milestone 11f):

- **Business Narrative Translation Layer** — registry-backed translation between Executive Reasoning and Executive Narrative
- `TranslationRegistry` with Preserve / Translate / Remove / Abstract categories
- `BusinessNarrativeTranslator` as single source of truth for executive terminology
- `executive_language.py` retained as compatibility layer delegating to the translator
- Transparency metadata filtered before metric extraction; person names abstracted for person-identifying dimensions only
- OpenAI narrative output post-processed to prevent jargon reintroduction
- Executive Narrative UX enhancements (assessment banner, split actions, structured confidence)
- Tests in `tests/test_business_narrative_translation.py` including end-to-end regression
- Documentation updated across ARCHITECTURE, HANDBOOK, ROADMAP, AI_COLLABORATION, CODING_STANDARDS, and README

---

## Milestone 12a — Branded Application Shell

Presentation-only UX milestone. No changes to analytics, AI behaviour, routing, clarification, or results logic.

### Delivered

* CRC-branded hero card with logo, org label, app title, subtitle, and capability badges
* Reusable shell modules: `ui/branding.py`, `ui/components/app_shell.py`
* Streamlit theme in `.streamlit/config.toml` (CRC-green primary accent)
* Sidebar workflow unchanged (dataset upload, samples, profile summary)
* AppTest helper `assert_app_shell_visible()` and bootstrap test updates

### Portfolio note

The shell modules are structured for reuse across future CRC portfolio applications with shared brand constants and hero rendering.

Completed in Phase 4 (Milestone 12a):

- Branded application shell — hero-owned CRC identity; functional sidebar unchanged
- `ui/branding.py` and `ui/components/app_shell.py`
- `.streamlit/config.toml` CRC-aligned theme
- AppTests updated; full regression suite passing

---

## Milestone 12b — Executive Narrative Mode Controls

Presentation and configuration milestone. Deterministic analytics, routing, clarification, and prompt construction unchanged.

### Runtime Narrative Configuration

* `NarrativeRuntimeConfig` (`enabled`, `provider`) resolves narrative enablement and provider selection
* Configuration precedence: **session state → environment defaults → hardcoded defaults**
* Streamlit session key: `narrative_mode` with internal values `off`, `deterministic`, `openai`
* Non-UI callers use `NarrativeRuntimeConfig.from_environment()` via `run_analysis(..., narrative_config=None)`

### Sidebar controls

* **Executive Summary** sidebar section with **Narrative Provider** radio (Deterministic Engine / OpenAI GPT)
* Provider status indicator updates immediately (Deterministic Engine active, OpenAI GPT active, OpenAI GPT unavailable)
* Help text explains both providers without requiring environment variables
* `NARRATIVE_MODE_OFF` remains for programmatic callers and tests; not exposed in the Streamlit sidebar (removed in Milestone 12d)

### Provider resolution

* `resolve_narrative(config)` returns `NarrativeResolution` (generator, requested/resolved provider, warnings)
* Missing OpenAI API key or init failure falls back to deterministic narrative with user-visible warning
* Deterministic analytics remain authoritative regardless of narrative mode

Completed in Phase 4 (Milestone 12b):

- Sidebar Narrative Provider runtime controls (two-provider UX finalised in Milestone 12d)
- Runtime configuration model and factory resolution
- UI overrides environment at runtime; env still seeds session defaults
- Tests in `tests/test_narrative_runtime_config.py` and extended AppTests

---

## Milestone 12c — Narrative Provider Verification

Architecture verification milestone. Narrative content, prompts, and analytics unchanged.

### Provider verification architecture

```
PromptArtifact → resolve_narrative(config) → generate_narrative()
    → NarrativeGenerationMetadata → NarrativeResponse → UI (Generated By)
```

* Backend owns truth: `NarrativeGenerationMetadata` records requested provider, actual provider, fallback usage, and `wall_clock_duration_ms`
* [`narrative_generation.py`](src/operational_intelligence/llm/narrative_generation.py) orchestrates resolution, timing, enrichment, and structured logging
* [`narrative_provider_registry.py`](src/operational_intelligence/llm/narrative_provider_registry.py) maps stable provider IDs to display names (future providers need no UI changes)

### Backend-driven UI verification

* Results panel displays **Generated By** from `narrative.generation_metadata` only — never from session state or environment
* Labels: Deterministic Engine, OpenAI GPT, Fallback to Deterministic Engine
* Secondary metadata: Model and Generation Time when available
* Legacy `generator_type` / `generation_duration_ms` fields remain synchronised for backward compatibility

### OpenAI runtime reliability

* `openai_client.py` injects OS-native certificate trust via `truststore` before OpenAI HTTP calls
* Supports corporate and Windows environments where default Python SSL bundles may fail
* Transient API failures retry with bounded attempts before surfacing an error to the fallback layer

### Structured logging

Each generation emits one log event with: requested provider, actual provider, generator name, wall-clock duration, fallback flag, and fallback reason.

Completed in Phase 4 (Milestone 12c):

- Narrative generation metadata model and orchestration layer
- Provider registry and structured logging
- Generated By verification in results UI (label finalised in Milestone 12d)
- OpenAI SSL truststore integration for provider reliability
- Tests in `tests/test_narrative_generation_metadata.py`

---

## Milestone 12d — Executive Narrative UX Refinement

Presentation-only milestone refining executive narrative UX without changing prompts, analytics, or provider verification architecture.

### Delivered

* Results section renamed to **Executive Summary** (provider-neutral)
* **Generated By** display with secondary Model and Generation Time metadata
* Sidebar simplified to **Narrative Provider** with Deterministic Engine and OpenAI GPT only
* Default provider is Deterministic Engine; narrative always available via sidebar selection
* Deterministic business language improvements in `business_narrative_translation.py`

Completed in Phase 4 (Milestone 12d):

- Executive Summary section and Generated By presentation
- Two-provider sidebar UX
- Business language refinements and updated AppTests

---

## Milestone 13b — Executive Results Information Architecture

Presentation-only milestone reorganising the results panel into a task-oriented information hierarchy without changing analytics, narrative generation, or backend models.

### Task-oriented flow

The results panel answers progressively deeper questions:

1. **Summary** — What happened? (Direct Answer, Executive Summary, Recommended Actions)
2. **Findings** — Why did it happen? (Analytical Findings, Executive Reasoning, Follow-Up Investigations)
3. **Audit & Verification** — Can I verify it? (System Transparency, Generated By, Technical Details, governance)

### Delivered

* **Analysis Header** — Analysis Complete status, question, dataset, completed timestamp, narrative provider when available
* Executive content block rendered before Investigation and Audit
* **Results Navigation** placeholder (`Overview | Investigation | Audit`) preparing Milestone 13c tab navigation
* Modular presentation components under `ui/components/` (`analysis_header`, `results_executive`, `results_investigation`, `results_audit`, `results_shared`)
* `AnalysisResult.completed_at` UI metadata set at analysis completion
* AppTests for section order and capability preservation

Completed in Phase 5 (Milestone 13b):

- Executive Results Information Architecture implemented
- Analysis Header and IA section grouping
- Audit section owns provider verification and governance presentation
- Tests in `tests/app/test_results_information_architecture.py`

---

## Milestone 13c — Executive-Focused Progressive Disclosure

Presentation-only milestone reducing default visible content while preserving every analytical capability.

### Executive Surface

Default post-analysis view (before opening disclosure groups):

* Analysis Header (Analysis Complete, question, dataset, timestamp, provider)
* Direct Answer
* Executive Summary — assessment banner, Key Message, Executive Actions (capped), Assessment Confidence summary line
* Recommended Actions — first three visible; remainder in **More recommendations**
* Narrative fallback warning when present

### Progressive disclosure

| Disclosure group | Label | Default | Contents |
|------------------|-------|---------|----------|
| Investigation | `Investigation` | Collapsed | Overview, Analytical Findings, Executive Reasoning, Follow-Up Investigations |
| Audit | `Audit & Verification` | Collapsed | System Transparency, Generated By, Technical Details, governance, runtime metadata |
| Executive Summary subsections | Section titles / `Details` / `Limitations` | Collapsed | Why This Matters, investigation guidance sections, confidence rationale, limitations |
| Dataset Preview | `Dataset Preview` | Collapsed after analysis | Existing preview table |

Completed in Phase 5 (Milestone 13c):

- Executive Surface and progressive disclosure
- Investigation and Audit & Verification disclosure groups
- Dataset Preview collapse after successful analysis
- Tests in `tests/app/test_progressive_disclosure.py`

---

## Milestone 13d — Results Tabs

Presentation-only milestone replacing top-level disclosure groups with task-oriented navigation.

### Tab model

| Tab | User question | Contents |
|-----|---------------|----------|
| Summary | What happened? | Direct Answer, Executive Summary (with inner expanders), Recommended Actions, narrative warnings |
| Findings | What evidence supports it? | Analytical Findings, evidence expanders, Executive Reasoning, Follow-Up Investigations |
| Audit & Verification | How was it produced? | System Transparency, Generated By, Technical Details, governance, runtime metadata |

Analysis Header (Analysis Complete metadata) renders **above** the tabs. Dataset Preview behaviour is unchanged.

Implementation: [`st.tabs()`](ui/components/results_panel.py) orchestration reusing [`results_executive.py`](ui/components/results_executive.py), [`results_investigation.py`](ui/components/results_investigation.py) (`render_findings_bundle`), and [`results_audit.py`](ui/components/results_audit.py). Analysis Overview was removed from the Findings tab as redundant with Summary and findings detail.

Tests: [`tests/app/test_results_tabs.py`](tests/app/test_results_tabs.py); tab-scoped helpers in [`tests/app/helpers.py`](tests/app/helpers.py).

Completed in Phase 5 (Milestone 13d):

- Results tabs (Summary / Findings / Audit & Verification)
- Tab-aware AppTests and golden journey updates

---

## Milestone 13e — Production Polish & Design System Foundation

Presentation-only milestone establishing a lightweight design system and polishing the executive experience for portfolio-ready MVP delivery.

### Design system foundation

Shared presentation tokens and helpers live in [`ui/results_presentation.py`](ui/results_presentation.py) (results zones, heading tiers, severity borders, evidence grids) and [`ui/branding.py`](ui/branding.py) (shell hero, muted panels, empty states, clarification styling).

Key helpers:

| Helper | Purpose |
|--------|---------|
| `render_level2_heading` / `render_level3_heading` | Consistent heading hierarchy by zone |
| `render_muted_panel` | Disabled narrative and bootstrap prompts |
| `render_empty_state` | Branded empty findings / evidence / follow-up states |
| `render_provider_status` | Unified sidebar and Audit provider feedback |
| `severity_panel_class` | Severity-coloured finding card borders |

### Delivered polish

* **Analyse** terminology standardised in the primary action button
* Direct Answer hero uses `.oic-direct-answer-card` (no collision with app hero `.oic-hero-card`)
* Executive Summary reads as a single briefing (muted disabled state, level-2 subsection headings)
* Narrative fallback warnings appear on **Summary** only (not duplicated in Audit)
* Audit transparency trail spacing and Generated By hierarchy
* Responsive metadata and evidence grids (`@media max-width: 720px`)

Completed in Phase 5 (Milestone 13e):

- Production polish and design system foundation
- Documentation aligned to Summary / Findings / Audit model

Next planned work:

See [REGRESSION.md](REGRESSION.md) for regression execution and [ROADMAP.md](ROADMAP.md) for milestone history.

---

# Future Direction

Future work includes:

- Expanded Application Testing
- Playwright Browser Testing
- LLM Narrative Generation
- LLM Evaluation Framework
- Workspace Management
- Multi-dataset Support
- Historical Analysis
- Production Deployment

---

# Definition of Success

The project will be considered successful if it demonstrates:

- Explainable AI
- Clean Architecture
- Production-quality Engineering
- Comprehensive Testing
- Reusable Components
- Professional Documentation
- Maintainable Code

Success is measured by engineering quality rather than feature count.

---

# Related Documentation

This handbook should be read alongside:

- ARCHITECTURE.md
- ROADMAP.md
- AI_COLLABORATION.md
- REGRESSION.md
- PERFORMANCE_BASELINES.md

Together these documents form the Operational Intelligence Copilot Engineering Knowledge Base.