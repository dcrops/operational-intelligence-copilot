# Operational Intelligence Copilot
# Engineering Handbook

**Version:** 1.0  
**Last Updated:** June 2026  
**Project Status:** Phase 3 complete — engineering-ready for Phase 4  
**Current Milestone:** Phase 4 — Milestone 11e — AI Executive Advisor

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

- **Executive Narrative (AI-Assisted)** section in results panel
- Pure presentation helpers in `ui/narrative_presentation.py`
- Governance caption when narrative renders; placeholder when disabled
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

Next planned work:

Phase 5 — LLM evaluation framework

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