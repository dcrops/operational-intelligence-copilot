# Operational Intelligence Copilot

# Roadmap

**Version:** 1.0
**Last Updated:** June 2026
**Current Phase:** Phase 4 — Presentation and polish (Milestone 12d complete)
**Current Milestone:** Milestone 12d — Executive Narrative UX Refinement (complete)

---

# Purpose

This document describes the current development roadmap for the Operational Intelligence Copilot.

It should be updated whenever a milestone is completed or when significant architectural decisions change the future direction of the project.

Unlike the Engineering Handbook, this document is expected to evolve throughout the life of the project.

---

# Project Vision

The Operational Intelligence Copilot aims to become a production-quality AI decision support platform capable of:

* Analysing operational datasets
* Producing explainable executive reports
* Supporting multiple organisations
* Combining deterministic and LLM-assisted reasoning
* Demonstrating production-quality AI Engineering practices

---

# Development Philosophy

The roadmap follows several principles:

* Small milestones
* Incremental delivery
* Continuous review
* Continuous testing
* Reusable infrastructure before features
* Deterministic capability before AI capability

Every milestone should leave the application in a stable, releasable state.

---

# Phase 1 — Deterministic Analytics ✅ Completed

Objective:

Build a deterministic analytical engine capable of analysing operational datasets.

Completed capabilities include:

* Dataset Profiling
* Intent Routing
* Clarification Engine
* Trend Analysis
* Variance Analysis
* Anomaly Detection
* Snapshot Intelligence
* Evidence Generation
* Transparency

Status:

**Completed**

---

# Phase 2 — Executive Reasoning ✅ Completed

Objective:

Transform deterministic findings into structured executive reasoning.

Completed capabilities include:

* Executive Themes
* Operational Assessment
* Executive Conclusions
* Priority Actions
* Executive Report Generation
* Executive Reasoning Presentation

Status:

**Completed**

---

# Phase 3 — Application Quality Engineering ✅ Completed

Objective:

Develop a production-quality testing strategy and application validation framework.

Status:

**Completed** (Milestone 10h — June 2026)

## Milestone 10a — Executive Reasoning Experience

Status:

✅ Completed

Highlights:

* Executive reasoning integrated into the Streamlit interface
* Report presentation refined
* Executive report sections standardised

---

## Milestone 10b — Golden Dataset Registry

Status:

✅ Completed

Highlights:

* Canonical datasets documented
* Regression capability matrix established
* Golden Dataset philosophy defined

---

## Milestone 10c — Application Testing Framework

Status:

✅ Completed

Highlights:

* Streamlit AppTest infrastructure
* Reusable application test helpers
* Golden Scenario Registry
* Initial smoke tests

---

## Milestone 10d — Golden User Journeys

Status:

✅ Completed

Highlights:

* Manufacturing behavioural journey
* Education snapshot journey
* Workforce clarification journey
* Reusable journey helpers expanded
* Behaviour-first application testing

---

## Planned Milestones

### Milestone 10e — Clarification Workflow Testing

Status:

✅ Completed

Highlights:

• Metric clarification workflows validated
• Dimension clarification workflows validated
• Clarification recovery behaviour validated
• Behaviour-first AppTests expanded
• Reusable clarification helpers extended

---

### Milestone 10f

Status

✅ Completed

Highlights:

Temporal filtering validated
Snapshot behaviour validated
Snapshot contributor transparency validated
Behavioural AppTests expanded

---

### Milestone 10g

Status

✅ Completed

Highlights

• Dataset onboarding validated
• Dataset replacement validated
• Invalid dataset recovery validated
• Dataset lifecycle behavioural testing completed

---

### Milestone 10h — Engineering Readiness & Regression

Status:

✅ Completed

Highlights:

* Regression runbook published (`docs/AI_ENGINEERING/REGRESSION.md`)
* Performance baselines documented (`docs/AI_ENGINEERING/PERFORMANCE_BASELINES.md`)
* Engineering documentation synchronised across Handbook, Architecture, Roadmap, and Technical Debt
* Profiling date-inference warning resolved at source (`format="mixed"`)
* Phase 3 declared engineering-ready for Phase 4

---

# Phase 4 — LLM Narrative Generation

Status:

🚧 In progress

Objective:

Introduce Large Language Models to improve report narration while preserving deterministic reasoning.

**Core principle:** the deterministic platform owns truth; the AI layer owns communication.

Deterministic analytics and executive reasoning remain the source of truth.

### Milestone 11a — AI Integration Boundary

Status:

✅ Completed

Objective:

Establish the architectural contract between deterministic analysis output and future LLM narrative generation.

Delivered:

* Frozen `NarrativeRequest` and `NarrativeResponse` models
* `NarrativeRequestBuilder` pure transformer
* `NarrativeGenerator` protocol
* `DeterministicNarrativeGenerator` placeholder (no external services)
* `OIC_NARRATIVE_ENABLED` feature flag (default off)
* Optional `AnalysisResult.narrative` attachment via `ui/narrative_service.py`
* Boundary tests in `tests/test_narrative_boundary.py`

Explicitly out of scope for 11a:

* OpenAI API calls, prompts, streaming, UI narrative rendering
* Changes to routing, clarification, analytics, or pipeline orchestration

### Milestone 11b — Prompt Construction & Narrative Assembly

Status:

✅ Completed

Objective:

Introduce a governed `PromptArtifact` layer as the vendor-neutral, AI-ready representation of deterministic evidence.

Delivered:

* `PromptArtifact`, `EvidenceReference`, and `GroundingConstraints` models
* `PromptArtifactBuilder` pure transformer from `NarrativeRequest`
* `narrative_governance.py` — grounding rules, objectives, artifact version
* `NarrativeGenerator` updated to consume `PromptArtifact`
* Prompt construction tests in `tests/test_prompt_construction.py`

Explicitly out of scope for 11b:

* OpenAI integration, prompt execution, UI narrative rendering
* Additional narrative objectives beyond `executive_narrative` and `executive_summary`

### Milestone 11c — OpenAI Adapter & First Narrative Generation

Status:

✅ Completed

Objective:

Integrate OpenAI as the first production `NarrativeGenerator` implementation while preserving deterministic analytics as authoritative.

Delivered:

* `OpenAINarrativeGenerator`, `OpenAIPromptFormatter`, `OpenAINarrativeResponseParser`
* `FallbackNarrativeGenerator` with explicit deterministic fallback
* `narrative_factory.py` with `OIC_NARRATIVE_PROVIDER` support
* `OpenAIProviderConfig`, `NarrativeGenerationError`
* Extended `NarrativeResponse` metadata (`model`, `generation_duration_ms`, `artifact_version`)
* OpenAI tests in `tests/test_openai_narrative_generator.py` (fake `LLMClient` only)

Explicitly out of scope for 11c:

* UI narrative rendering, streaming, memory, agents, evaluation framework
* Token/cost tracking, prompt versioning

### Milestone 11d — Executive Narrative Rendering

Status:

✅ Completed

Objective:

Render optional AI-assisted executive narrative in the Streamlit results panel while preserving deterministic report sections as authoritative.

Delivered:

* `ui/narrative_presentation.py` — pure presentation helpers and governance copy
* Results panel renders executive narrative when `result.narrative` is present (section renamed **Executive Summary** in Milestone 12d)
* Placeholder when narrative is absent (non-UI callers with narrative disabled only; sidebar always selects a provider after 12d)
* Presentation unit tests and minimal AppTests (deterministic provider only)

Explicitly out of scope for 11d:

* Prompt/adapter changes, evaluation framework, narrative editing, streaming

### Milestone 11e — AI Executive Advisor

Status:

✅ Completed

Objective:

Evolve the AI narrative layer from summarisation into executive communication and decision support while keeping deterministic analytics authoritative.

Delivered:

* Reusable `NarrativeSection` model with ordered advisor sections in `NarrativeResponse.sections`
* Executive-advisor prompt contract (Key Message through Recommended Next Steps) with plain-language and hypothesis governance
* **Executive Context Builder** (`executive_context_builder.py`) — domain-agnostic translation from deterministic outputs to executive business context
* `ExecutiveContext` embedded in `PromptArtifact`; narrative generators consume executive context, not raw telemetry
* Dimension-aware investigation guidance grounded in pipeline metadata only
* Deterministic provider produces the same advisor section structure as graceful fallback
* UI renders sections dynamically without hard-coded advisor field names
* Tests in `tests/test_executive_advisor_narrative.py` and `tests/test_executive_context_builder.py`

Explicitly out of scope for 11e:

* Results page redesign, evidence redesign, charts, drill-down workflows, new analytics, hallucination scoring, streaming, memory, agents, RAG, feedback collection, multi-model comparison

### Milestone 11f — Business Narrative Translation Layer

Status:

✅ Completed

**Summary:** Milestone 11f introduced the Business Narrative Translation Layer, separating executive communication from deterministic reasoning through a reusable registry-driven translation architecture.

Objective:

Introduce a registry-backed translation layer between Executive Reasoning and Executive Narrative so executives see business concepts only — not routing metadata, tool names, or person-identifying record values.

Delivered:

* `business_narrative_translation.py` — `TranslationRegistry`, `BusinessNarrativeTranslator`, Preserve / Translate / Remove / Abstract categories
* Data-driven terminology registry with singular/plural support for future extension
* `executive_language.py` retained as compatibility layer delegating to the translator
* Registry-driven transparency filtering in `ExecutiveContextBuilder`
* Reasoning trace translation at narrative snapshot boundary
* OpenAI narrative post-processing to prevent jargon reintroduction
* Executive Narrative UX enhancements (assessment banner, split actions, structured confidence)
* Tests in `tests/test_business_narrative_translation.py` including end-to-end regression

Explicitly out of scope for 11f:

* Analytics, routing, Executive Reasoning engine, System Transparency formatters, evidence generation changes
* Unifying UI metric humanisation with narrative registry (future consistency work)

### Milestone 12a — Branded Application Shell

Status:

✅ Completed

**Summary:** Milestone 12a introduced a CRC-branded application shell with a professional hero card, capability badges, and Streamlit theme alignment — presentation-only, with no analytical or AI behaviour changes.

Objective:

Create a portfolio-ready branded shell aligned with CHASE RISK & COMPLIANCE identity while keeping sidebar workflow unchanged.

Delivered:

* [`ui/branding.py`](ui/branding.py) — brand constants, logo path, capability badges, minimal shell CSS
* [`ui/components/app_shell.py`](ui/components/app_shell.py) — reusable `render_app_hero()` for CRC portfolio apps
* Branded hero with CRC logo, org label, app title, subtitle, and capability badges
* [`.streamlit/config.toml`](.streamlit/config.toml) — CRC-green primary theme
* AppTest updates (`assert_app_shell_visible`)

Explicitly out of scope for 12a:

* Results page redesign, sidebar branding, analytics, narrative, routing, or provider changes

### Milestone 12b — Executive Narrative Mode Controls

Status:

✅ Completed

**Summary:** Milestone 12b added sidebar **Narrative Provider** runtime controls with session overrides taking precedence over environment variables, provider status display, and graceful OpenAI fallback — without changing deterministic analytics. Milestone 12d simplified the sidebar to Deterministic Engine and OpenAI GPT only.

Delivered:

* `NarrativeRuntimeConfig` and `NarrativeResolution` for explicit runtime provider selection
* [`ui/narrative_runtime.py`](ui/narrative_runtime.py) — session state mapping and precedence
* [`ui/components/narrative_controls.py`](ui/components/narrative_controls.py) — sidebar provider selector, help text, provider status
* Config threaded through `run_analysis()` → `maybe_generate_narrative()` → `resolve_narrative()`
* Environment variables remain supported as session defaults for dev/CI/non-UI callers
* AppTests and unit tests for mode selection, override, fallback, and provider status

Explicitly out of scope for 12b:

* Analytics, routing, prompt construction, results layout, branding shell changes

### Milestone 12c — Narrative Provider Verification

Status:

✅ Completed

**Summary:** Milestone 12c added backend-driven generation metadata, a narrative orchestration layer, structured logging, and UI verification of the provider that actually generated the executive summary — without changing narrative content or analytics. Milestone 12d renamed the results label to **Generated By**.

Delivered:

* `NarrativeGenerationMetadata` on `NarrativeResponse` (requested/actual provider, fallback, wall-clock timing)
* [`narrative_provider_registry.py`](src/operational_intelligence/llm/narrative_provider_registry.py) — stable provider IDs and display names
* [`narrative_generation.py`](src/operational_intelligence/llm/narrative_generation.py) — orchestration, metadata enrichment, structured logging
* Backend-driven **Generated By** display in results (Deterministic Engine, OpenAI GPT, Fallback to Deterministic Engine)
* `truststore` in `openai_client.py` for OS-native SSL certificate verification when calling OpenAI
* Tests in [`tests/test_narrative_generation_metadata.py`](tests/test_narrative_generation_metadata.py)

Explicitly out of scope for 12c:

* OpenAI prompt quality, executive narrative wording, analytics, sidebar controls, branding

### Milestone 12d — Executive Narrative UX Refinement

Status:

✅ Completed

**Summary:** Milestone 12d refined executive narrative presentation with provider-neutral language: renamed the results section to **Executive Summary**, renamed **Generated By** with secondary metadata, simplified sidebar to two narrative providers, and improved deterministic business language.

Delivered:

* Results section renamed from Executive Narrative (AI-Assisted) to **Executive Summary**
* **Generated By** provider display with Model and Generation Time secondary metadata
* Sidebar **Narrative Provider** with Deterministic Engine and OpenAI GPT only (no Disabled option)
* Deterministic business language refinements in translation registry
* Updated AppTests and presentation tests

Future milestones (planned):

* LLM evaluation framework

---

# Phase 5 — LLM Evaluation Framework

Status:

📋 Planned

Objective:

Evaluate LLM-generated outputs using deterministic benchmarks.

Potential capabilities:

* Golden answer comparisons
* Prompt evaluation
* Quality scoring
* Regression evaluation
* Hallucination detection

---

# Phase 6 — Workspace & Dataset Management

Status:

📋 Planned

Objective:

Transform the application from analysing a single CSV into managing multiple organisational datasets.

Potential capabilities:

* Dataset library
* Workspace management
* Multiple organisations
* Historical analyses
* Dataset versioning
* Saved reports

---

# Long-Term Vision

The project should ultimately demonstrate:

* Production-quality AI Engineering
* Explainable AI
* Deterministic analytical reasoning
* AI-assisted executive reporting
* Comprehensive automated testing
* Clean architecture
* Professional engineering documentation

The application should serve both as a portfolio project and as a reference implementation for engineering AI systems responsibly.

---

# Milestone Workflow

Every milestone follows the same lifecycle:

```text
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

Implementation

↓

Human Review

↓

Testing

↓

Git Commit

↓

Roadmap Update
```

No milestone is considered complete until it has been:

* Reviewed
* Tested
* Documented
* Committed

---

# Success Criteria

The project roadmap will be considered successful if it delivers:

* Stable deterministic analytics
* Explainable executive reasoning
* Production-quality testing
* LLM-enhanced reporting
* Professional engineering practices
* High-quality documentation
* A compelling AI Engineering portfolio

---

# Related Documentation

This roadmap should be read alongside:

* ENGINEERING_HANDBOOK.md
* ARCHITECTURE.md
* AI_COLLABORATION.md

Together these documents describe the engineering standards, architecture, collaboration model, and future direction of the Operational Intelligence Copilot.

# Future Considerations

The following items have been identified as potential future enhancements.
They are intentionally outside the current engineering roadmap and will be
prioritised once the core application reaches MVP.

## Dataset Management

- Support Excel (.xlsx) upload through a dedicated Dataset Loader abstraction.
- Support multiple uploaded datasets within a workspace.
- Enable cross-dataset analytical comparisons.
- Introduce dataset versioning and dataset identity management.
- Support saved analysis sessions.

## Future Analytics

(Add future ideas here as they arise.)

## Future Engineering

(Add engineering improvements here.)
