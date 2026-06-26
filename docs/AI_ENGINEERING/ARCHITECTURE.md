# Operational Intelligence Copilot

# Architecture

**Version:** 1.1
**Last Updated:** June 2026  
**Current Milestone:** Phase 4 — Milestone 11f — Business Narrative Translation Layer

---

# Purpose

This document describes the current software architecture of the Operational Intelligence Copilot.

It provides a high-level overview of the major components, their responsibilities, and the flow of information through the system.

This document intentionally focuses on architecture rather than implementation details.

---

# Architectural Goals

The architecture has been designed around the following principles:

* Domain agnostic
* Explainable
* Deterministic
* Modular
* Testable
* Extensible
* Production-oriented

The application separates analytical reasoning from presentation and future LLM capabilities.

---

# High-Level Pipeline

```text
Dataset
    │
    ▼
Dataset Profiling
    │
    ▼
Intent Routing
    │
    ▼
Clarification Detection
    │
    ▼
Analytical Tool Selection
    │
    ▼
┌──────────────────────────────┐
│ Analytical Tools             │
│                              │
│ • Trend Analysis             │
│ • Variance Analysis          │
│ • Anomaly Detection          │
│ • Snapshot Analysis          │
└──────────────────────────────┘
    │
    ▼
Evidence Generation
    │
    ▼
Risk Assessment
    │
    ▼
Executive Reasoning
    │
    ▼
Executive Report
    │
    ├──────────────────────────────────────┐
    │                                      │
    ▼                                      ▼
Presentation Layer              Business Narrative Translation Layer
(Direct Answer, Executive                  │
 Reasoning, Transparency)                 ▼
    │                              Executive Narrative
    │                                      │
    └──────────────────┬───────────────────┘
                       ▼
              Application Testing
```

The deterministic pipeline (through Executive Report) remains the single source of analytical truth. The optional narrative path applies audience-specific translation before Executive Narrative generation.

---

# Presentation Pipeline

The user-facing report combines deterministic presentation with optional executive narrative communication.

```text
Question
    │
    ▼
Intent Routing
    │
    ▼
Deterministic Analytics
    │
    ▼
Executive Reasoning
    │
    ▼
Business Narrative Translation Layer
    │
    ▼
Executive Narrative
    │
    ▼
Presentation
```

This pipeline separates **analytical reasoning** (Executive Reasoning, System Transparency) from **executive communication** (Executive Narrative). The translation layer ensures the same deterministic evidence can be presented appropriately to each audience without modifying underlying analytics or reasoning.

---

# Layer Responsibilities

## Dataset Layer

Responsible for:

* Loading CSV datasets
* Dataset validation
* Dataset selection
* Future multi-dataset support

The dataset layer should remain independent of analytical logic.

---

## Dataset Profiling

Automatically analyses uploaded datasets.

Produces:

* potential metrics
* potential dimensions
* date columns
* identifier columns
* suggested analytical tools

The remainder of the application depends upon the generated profile rather than hardcoded schemas.

---

## Intent Routing

Determines what analytical task the user is requesting.

Examples include:

* trend analysis
* variance analysis
* anomaly detection
* snapshot analysis

Intent routing determines which analytical tool should execute.

---

## Clarification Engine

Detects ambiguity before analysis begins.

Examples include:

* missing metric
* missing dimension
* ambiguous terminology

The objective is to avoid making unsupported assumptions.

---

## Analytical Layer

The analytical layer performs deterministic calculations.

Current analytical tools include:

* Trend Analysis
* Variance Analysis
* Anomaly Detection
* Snapshot Analysis

Analytical tools do not generate conclusions.

They generate evidence only.

---

## Evidence Layer

Evidence represents structured analytical output.

Evidence should remain deterministic and traceable.

Evidence forms the input to later reasoning layers.

---

## Risk Assessment

Converts analytical evidence into structured findings.

Findings provide a common representation that can be consumed by the reasoning layer.

---

## Executive Reasoning

The Executive Reasoning layer transforms findings into executive-level reasoning.

Current components include:

* Executive Themes
* Operational Assessment
* Executive Conclusions
* Priority Actions

This layer performs deterministic reasoning.

It does not perform analytical calculations.

---

## Executive Report

Aggregates all report content into a single structured object.

This report becomes the contract between backend reasoning and presentation.

The presentation layer should not perform additional reasoning.

---

## Presentation Layer

Implemented using Streamlit.

Responsible only for:

* rendering reports
* displaying reasoning
* displaying transparency
* accepting user interaction

Presentation should never contain business logic.

---

## AI Narrative Layer

Phase 4 introduces an optional AI narrative layer that sits **after** deterministic analysis completes.

**Core principle:** the deterministic platform owns truth; the AI layer owns communication.

The narrative layer may:

* summarise deterministic findings
* improve readability
* create executive narrative
* adapt tone
* explain deterministic evidence

The narrative layer must not:

* calculate metrics
* invent findings
* change risk levels
* override deterministic conclusions
* select analytical tools
* perform routing
* resolve clarification
* mutate pipeline results
* become the source of truth

### Boundary flow (Milestones 11a–11f)

```
AnalysisResult / ExecutiveReport snapshot
        ↓
NarrativeRequestBuilder
        ↓
NarrativeRequest
        ↓
BusinessNarrativeTranslator (filter, translate, abstract)
        ↓
ExecutiveContextBuilder
        ↓
ExecutiveContext
        ↓
PromptArtifactBuilder
        ↓
PromptArtifact
        ↓
resolve_narrative(config)
        ↓
generate_narrative()  (orchestration, timing, metadata, logging)
        ↓
NarrativeGenerator (+ post-translation for OpenAI output)
        ↓
NarrativeResponse (+ NarrativeGenerationMetadata)
        ↓
Executive UI (Streamlit results panel — Generated By from metadata)
```

Implementation lives under `src/operational_intelligence/llm/`:

* `narrative_models.py` — frozen `NarrativeRequest`, `NarrativeResponse`, `NarrativeGenerationMetadata`, `NarrativeSection`, `ExecutiveContext`, `PromptArtifact`, `EvidenceReference`, `GroundingConstraints`
* `business_narrative_translation.py` — registry-backed Business Narrative Translation Layer (Preserve / Translate / Remove / Abstract)
* `executive_context_builder.py` — translates deterministic outputs into domain-agnostic executive business context
* `executive_language.py` — compatibility layer delegating to `BusinessNarrativeTranslator`
* `narrative_builder.py` — pure transformer from deterministic snapshots to `NarrativeRequest`
* `prompt_artifact_builder.py` — pure transformer from `NarrativeRequest` to `PromptArtifact`
* `narrative_governance.py` — grounding rules, narrative objectives, artifact version
* `narrative_protocol.py` — `NarrativeGenerator` interface (consumes `PromptArtifact`)
* `narrative_factory.py` — resolves provider-specific generators (`NarrativeResolution`)
* `narrative_generation.py` — orchestrates generation, metadata enrichment, structured logging (Milestone 12c)
* `narrative_provider_registry.py` — stable provider IDs and display names (Milestone 12c)
* `openai_narrative_generator.py` — OpenAI adapter (Milestone 11c)
* `openai_prompt_formatter.py` — provider-specific message formatting
* `openai_response_parser.py` — labelled response parsing
* `fallback_narrative_generator.py` — resilient fallback to deterministic output
* `deterministic_narrative_generator.py` — deterministic placeholder
* `narrative_config.py` — `OIC_NARRATIVE_ENABLED`, `OIC_NARRATIVE_PROVIDER`, `OIC_OPENAI_MODEL`

### PromptArtifact layer (Milestone 11b)

`PromptArtifact` is the vendor-neutral, AI-ready representation of deterministic evidence. It contains structured `EvidenceReference` entries, `GroundingConstraints`, and a narrative objective — but no API provider details, model names, routing metadata, or pipeline internals.

**Future generators must treat PromptArtifact evidence as the complete set of citeable facts.**

`GroundingConstraints.closed_world = True` encodes the closed-world evidence contract. Prohibited behaviours include calculating metrics, infering causation, changing risk levels, introducing new findings, and overriding the direct answer.

### Provider architecture (Milestone 11c)

**OpenAI is a communication adapter only; deterministic analytics remain authoritative.**

| Variable | Default | Purpose |
|----------|---------|---------|
| `OIC_NARRATIVE_ENABLED` | off | Master narrative switch |
| `OIC_NARRATIVE_PROVIDER` | `deterministic` | `deterministic` or `openai` |
| `OIC_OPENAI_MODEL` | `gpt-4.1-mini` | Model for OpenAI adapter |
| `OPENAI_API_KEY` | unset | Required for OpenAI calls |

When provider is `openai`, `FallbackNarrativeGenerator` wraps `OpenAINarrativeGenerator` with `DeterministicNarrativeGenerator` as fallback. On timeout, auth failure, network error, rate limiting, or malformed response, the application continues with deterministic narrative and explicit limitations text — failure is not silent.

`OpenAIClient` (`openai_client.py`) uses the `truststore` package to inject OS-native SSL certificate trust before HTTP calls, improving reliability on Windows and corporate networks. Transient API errors are retried with bounded attempts before the fallback layer handles the failure.

When enabled, `AnalysisResult.narrative` may hold a `NarrativeResponse`. Deterministic fields remain unchanged.

### Provider verification (Milestone 12c)

The backend records authoritative generation metadata on each narrative run:

| Field | Purpose |
|-------|---------|
| `requested_provider` | Provider selected by runtime config |
| `actual_provider` | Provider that generated the narrative |
| `fallback_used` | Whether actual differed from requested |
| `wall_clock_duration_ms` | End-to-end generation elapsed time |
| `generator_name` | User-facing provider label from registry |

`generate_narrative()` in `narrative_generation.py` orchestrates resolution, timing, metadata attachment, and structured logging. The UI **Generated By** display reads `NarrativeGenerationMetadata` only — not sidebar selection or environment variables.

Legacy `generator_type` and `generation_duration_ms` on `NarrativeResponse` remain synchronised for backward compatibility.

### AI Executive Advisor (Milestone 11e)

Deterministic analytics answer **what happened**. The AI Executive Advisor answers **why it matters**, **where to investigate**, and **what to do next**.

`NarrativeResponse` contains ordered `NarrativeSection` objects rather than fixed advisor field names. This keeps parsers, renderers, and tests extensible as future outputs add sections (for example Business Impact, Risk Level, or export formats) without repeatedly changing the core contract.

Advisor sections (in order):

1. Key Message
2. Why This Matters
3. Where To Investigate First
4. Possible Explanations To Check
5. Executive Actions
6. Operational Investigation

`limitations` remains a separate field. Investigation guidance references dataset dimensions only when present in deterministic evidence.

Presentation metadata includes a deterministic Executive Assessment banner and structured Assessment Confidence block.

## Business Narrative Translation Layer

The Business Narrative Translation Layer is responsible for converting deterministic analytical artefacts into executive-facing business language before narrative generation.

Its purpose is to ensure that executive communication describes operational meaning rather than implementation details.

It provides a clean separation between analytical reasoning and executive presentation.

Implementation: `src/operational_intelligence/llm/business_narrative_translation.py` (`TranslationRegistry`, `BusinessNarrativeTranslator`). The layer does not modify analytics, routing, Executive Reasoning, System Transparency, or evidence generation.

```
Executive Reasoning (detailed, analytical)
        ↓
Deterministic snapshot (raw artefacts)
        ↓
Business Narrative Translation Layer
        ↓
Executive Context Builder
        ↓
Executive Narrative (business-facing)
        ↓
Presentation
```

### Separation of concerns

| Layer | Audience | Terminology |
|-------|----------|-------------|
| Direct Answer | Business user | Plain operational answer |
| Executive Reasoning | Operational leaders | Detailed, analytically accurate |
| System Transparency | Developer and auditor | Raw routing metadata, inferred parameters, tool names |
| Executive Narrative | Executive decision support | Business concepts only via translation registry |

### Preserve

Business concepts that should remain unchanged.

Examples:

* Attendance Rate
* Overtime Hours
* Behaviour Incidents
* Revenue
* Operational entities such as production lines, schools, departments, and branches (for example Line B, School C, Finance Department)

### Translate

Technical terminology converted into business terminology.

Examples:

| Internal | Executive |
|----------|-----------|
| `employee_name` | Employee |
| `department_name` | Department |
| `variance_analysis` | Performance comparison |
| `anomaly_detection` | Performance anomalies |

Translation is deterministic and registry-driven. Terminology entries support singular and plural forms for future extension.

### Remove

Implementation details that should never appear in executive communication.

Examples:

* Metric selected
* Aggregation inferred
* Comparison direction inferred
* Routed tools
* Internal routing metadata
* Analytical process telemetry (finding counts, tool titles)

### Abstract

Person-identifying values converted into executive-safe language.

Examples:

| Value | Executive (person dimension) |
|-------|------------------------------|
| Hayden King | Individual employee |
| Student Name (record value) | Individual student |
| Patient Name (record value) | Individual patient |

Operational entities such as departments, schools, production lines, and branches remain unchanged. Abstraction applies to person-identifying dimensions only (for example `employee_name`, `student_name`, `patient_name`).

### Design principles

* **Deterministic translation** — same input always produces the same executive output; no LLM involvement in the translation layer itself
* **Data-driven registry** — rules live in `TranslationRegistry`; extend terminology and remove-prefix lists rather than scattering conditionals
* **Presentation-only transformation** — translation affects narrative presentation, not analytical facts or reasoning outputs
* **Preserved internal identifiers** — `translate_identifier_with_source()` retains source identifiers alongside display labels for traceability and future drill-down
* **Preserved deterministic ordering** — translation never reorders metrics, dimensions, findings, or investigation targets

Translation is applied at three boundaries:

1. **Snapshot boundary** — `reasoning_trace` theme labels translated in `ui/narrative_service.py`
2. **Context boundary** — `ExecutiveContextBuilder` consumes registry-filtered transparency lines and translated prose
3. **OpenAI boundary** — parsed LLM sections post-processed through `translate_prose` to prevent jargon reintroduction

`executive_language.py` remains a compatibility layer delegating to `BusinessNarrativeTranslator`.

### Executive Context Builder (Milestone 11e)

The **Executive Context Builder** consumes output from the Business Narrative Translation Layer and assembles structured `ExecutiveContext` for narrative generation.

It performs **context assembly and template construction only** — it does not analyse, mutate findings, or infer unsupported causes.

Deterministic analytics answer **what happened**. Executive Context assembles that output into **executive decision support**: business significance, operational implications, investigation strategy, decision guidance, hypothesis categories, and action-oriented next steps. It deliberately avoids repeating analytical telemetry (finding counts, detection process wording, and implementation details) that already appear in Evidence and System Transparency.

Technical implementation details (z-scores, thresholds, analysed columns, detection algorithms) remain in Evidence and System Transparency; they are abstracted before narrative generation.

The builder is **intentionally domain-agnostic**. It does not encode industry-specific knowledge. Investigation targets, affected metrics, and business summaries are derived from metadata already produced by the analytical pipeline (for example dimension labels in transparency trails).

Both `DeterministicNarrativeGenerator` and `OpenAINarrativeGenerator` consume `ExecutiveContext` via `PromptArtifact.executive_context`. OpenAI prompt formatting uses executive evidence references rather than raw analytical telemetry.

### UI narrative rendering (Milestone 11d / 11e)

When `AnalysisResult.narrative` is present, the results panel renders an **Executive Summary** section at the end of the report. Deterministic sections (Direct Answer, Executive Reasoning, System Transparency, etc.) remain above it and authoritative.

Presentation helpers live in `ui/narrative_presentation.py`. The section includes **Generated By** metadata, governance copy, dynamically rendered `NarrativeSection` headings and content, and Limitations. The Streamlit sidebar always selects Deterministic Engine or OpenAI GPT (Milestone 12d); a placeholder info message appears only when narrative generation is skipped (for example programmatic `NarrativeRuntimeConfig.disabled()` callers).

**OpenAI is a communication adapter only; deterministic analytics remain authoritative.**

---

## Testing Layer

Testing is treated as a first-class architectural component.

Current testing layers include:

* Unit Tests
* Integration Tests
* Streamlit AppTests
* Golden Dataset Registry
* Golden User Journeys

Future additions include:

* Playwright browser tests
* LLM evaluation
* Performance regression

---

# Architectural Boundaries

The project deliberately separates responsibilities.

```
Analytics

↓

Evidence

↓

Reasoning

↓

Business Narrative Translation (narrative path only)

↓

Presentation
```

Analytical reasoning (Executive Reasoning, System Transparency) and executive communication (Executive Narrative) remain distinct. Transparency retains raw deterministic terminology; Executive Narrative consumes translated business language only.

These boundaries should remain intact.

Avoid introducing presentation logic into analytical components.

Avoid introducing analytical behaviour into presentation components.

---

# Current Major Components

Current high-level modules include:

* Dataset Profiler
* Intent Router
* Clarification Engine
* Trend Analysis Tool
* Variance Analysis Tool
* Anomaly Detection Tool
* Snapshot Analysis Tool
* Risk Assessment Engine
* Executive Reasoning Engine
* Executive Report Generator
* Answer Generator
* Transparency Engine
* Business Narrative Translation Layer (`business_narrative_translation.py`)
* Executive Context Builder
* Narrative generators (deterministic / OpenAI)

---

# Current Repository Organisation

The repository is organised into logical engineering areas.

Examples include:

```text
src/
    operational_intelligence/

tests/

ui/

docs/

data/
```

Future architectural changes should preserve this modular organisation.

---

# Current Testing Architecture

The project currently follows a layered testing strategy.

```
Unit Tests

↓

Integration Tests

↓

Application Tests

↓

Future Browser Tests

↓

Future LLM Evaluation
```

Testing infrastructure should remain reusable.

Golden datasets and golden scenarios should be reused across multiple testing layers.

---

# Future Architecture

The current architecture intentionally leaves room for future capabilities.

Planned architectural additions include:

* Multi-dataset workspaces
* Historical dataset collections
* LLM narrative generation
* LLM evaluation framework
* Agentic workflow orchestration
* Production deployment
* Multi-organisation support

These capabilities should extend the existing architecture rather than replace it.

---

# Architectural Principles

The following principles should guide future development.

* Maintain deterministic reasoning.
* Separate analytics from reasoning.
* Separate reasoning from presentation.
* Separate executive communication from analytical transparency.
* Reuse infrastructure before adding features.
* Protect module boundaries.
* Prefer composition over duplication.
* Optimise for maintainability.
* Build for explainability.

---

# Related Documentation

This document should be read alongside:

* ENGINEERING_HANDBOOK.md
* ROADMAP.md
* AI_COLLABORATION.md

Together these documents describe how the Operational Intelligence Copilot is engineered, implemented, and evolved.
