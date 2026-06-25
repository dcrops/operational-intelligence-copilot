# Operational Intelligence Copilot

# Architecture

**Version:** 1.0
**Last Updated:** June 2026  
**Current Milestone:** Phase 3 complete — Application Quality Engineering

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
    ▼
Presentation Layer
    │
    ▼
Application Testing
```

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

### Boundary flow (Milestones 11a–11c)

```
AnalysisResult / ExecutiveReport snapshot
        ↓
NarrativeRequestBuilder
        ↓
NarrativeRequest
        ↓
PromptArtifactBuilder
        ↓
PromptArtifact
        ↓
resolve_narrative_generator()
        ↓
NarrativeGenerator
        ↓
NarrativeResponse
```

Implementation lives under `src/operational_intelligence/llm/`:

* `narrative_models.py` — frozen `NarrativeRequest`, `NarrativeResponse`, `PromptArtifact`, `EvidenceReference`, `GroundingConstraints`
* `narrative_builder.py` — pure transformer from deterministic snapshots to `NarrativeRequest`
* `prompt_artifact_builder.py` — pure transformer from `NarrativeRequest` to `PromptArtifact`
* `narrative_governance.py` — grounding rules, narrative objectives, artifact version
* `narrative_protocol.py` — `NarrativeGenerator` interface (consumes `PromptArtifact`)
* `narrative_factory.py` — resolves provider-specific generators
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

When enabled, `AnalysisResult.narrative` may hold a `NarrativeResponse`. Deterministic fields remain unchanged. UI narrative rendering is deferred to a later milestone.

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

Presentation
```

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
