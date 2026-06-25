# Operational Intelligence Copilot

> A production-quality AI Engineering portfolio project demonstrating deterministic analytics, explainable reasoning, behavioural testing, and engineering discipline before introducing Large Language Models.

---

## Overview

Operational Intelligence Copilot is an AI Engineering project that transforms operational datasets into executive-level analytical insights using a deterministic reasoning pipeline.

Unlike many AI demonstrations that immediately rely on Large Language Models, this project intentionally establishes a robust deterministic foundation first.

The objective is to demonstrate the engineering required to build trustworthy AI systems before introducing probabilistic AI capabilities.

The project focuses on:

* Deterministic analytical reasoning
* Explainable decision making
* Behavioural application testing
* Engineering governance
* Production-quality software architecture

---

## Why this project exists

Many AI portfolio projects demonstrate prompt engineering or simple integrations with LLM APIs.

This project deliberately explores a different engineering philosophy.

Rather than allowing an LLM to determine analytical facts, the system first establishes a deterministic analytical pipeline capable of:

* profiling datasets
* selecting analytical strategies
* performing deterministic analytics
* producing executive findings
* explaining every analytical decision

Only after this deterministic platform is complete, an AI Narrative Layer communicates those findings through audience-specific presentation — including the Business Narrative Translation Layer for executive-facing language.

This approach reflects modern AI Engineering practices where AI augments reliable systems instead of replacing them.

---

# Key Features

## Deterministic Analytics

Automatically profiles uploaded operational datasets and selects appropriate analytical strategies including:

* Trend Analysis
* Variance Analysis
* Anomaly Detection
* Risk Assessment

---

## Executive Reasoning

Produces executive-focused reasoning including:

* Direct Answer
* Analysis Overview
* Analytical Findings
* Executive Reasoning
* Operational Assessment
* Executive Conclusions
* Priority Actions

---

## Explainability

Every analysis includes complete transparency.

The application explains:

* selected analytical tools
* inferred metrics
* inferred dimensions
* aggregation strategy
* temporal reasoning
* clarification decisions
* evidence used during analysis

System Transparency retains raw deterministic metadata. Executive Narrative applies the Business Narrative Translation Layer so executives see business language only.

---

## Executive Narrative (AI-Assisted)

Optional executive briefing generated from deterministic evidence:

* Business Narrative Translation Layer providing deterministic translation from analytical reasoning into executive-facing business language
* Executive advisor sections (Key Message, Why This Matters, investigation guidance, executive and operational actions)
* Deterministic or OpenAI-backed generation with explicit limitations
* Executive Assessment banner and structured confidence presentation

---

## Intelligent Clarification

Broad or ambiguous questions trigger clarification workflows allowing users to resolve intent before analysis begins.

Examples:

* Analyse this dataset
* Which metric?
* Which dimension?

---

## Temporal Intelligence

Automatically recognises temporal questions including:

* monthly analysis
* quarterly analysis
* yearly analysis
* snapshot analysis

Example:

> "How has attendance changed in April 2026?"

The application automatically activates Snapshot Mode and explains why.

---

## Behavioural Application Testing

The project includes a comprehensive behavioural testing framework built using Streamlit AppTest.

Coverage includes:

* Golden User Journeys
* Clarification Workflows
* Temporal Behaviour
* Snapshot Behaviour
* Dataset Lifecycle
* Engineering Regression

Tests validate user-visible behaviour rather than implementation details.

---

# Architecture

The application follows a layered architecture.

```text
User Interface (Streamlit)

        │

        ▼

Application Orchestration

        │

        ▼

Deterministic Reasoning Pipeline

        │

        ▼

Analytics Engine

        │

        ▼

Evidence Generation

        │

        ▼

Executive Reporting

        │

        ├─────────────────────────────┐
        │                             │
        ▼                             ▼
System Transparency          Business Narrative Translation Layer
(Direct Answer, Executive              │
 Reasoning — analytical)               ▼
        │                      Executive Narrative
        │                             │
        └──────────────┬──────────────┘
                       ▼
                 Presentation
```

The deterministic pipeline remains the single source of analytical truth.

Executive Reasoning and System Transparency present analytical and audit detail. The Business Narrative Translation Layer converts the same evidence into executive-facing business language before Executive Narrative generation.

Future AI capabilities enhance executive communication rather than replace analytical reasoning.

---

# Engineering Highlights

The project demonstrates production-quality engineering practices including:

* Layered architecture
* Strong separation of concerns
* Pydantic domain models
* Deterministic reasoning
* Behaviour-driven application testing
* Golden Dataset Registry
* Golden Scenario Registry
* Engineering documentation
* Regression documentation
* Performance baselines
* Architecture reviews
* Technical debt management

---

# Technology Stack

* Python
* Streamlit
* Pandas
* NumPy
* Pydantic
* Pytest
* Streamlit AppTest

---

# Project Structure

```text
src/
    operational_intelligence/

tests/
    unit/
    app/

data/
    sample/

docs/
    AI_ENGINEERING/
```

The engineering documentation describes the architectural decisions and development workflow in detail.

---

# Running the Project

Clone the repository.

Install dependencies.

Run the Streamlit application.

```bash
streamlit run app.py
```

---

# Running Tests

Targeted behavioural tests

```bash
python -m pytest tests/app/test_<area>.py -m app -q
```

All behavioural application tests

```bash
python -m pytest -m app -q
```

Full regression suite

```bash
python -m pytest -q
```

Further information is available in:

```
docs/AI_ENGINEERING/REGRESSION.md
```

---

# Engineering Documentation

The repository includes a complete Engineering Knowledge Base.

* ENGINEERING_HANDBOOK.md
* ARCHITECTURE.md
* ROADMAP.md
* AI_COLLABORATION.md
* CODING_STANDARDS.md
* REGRESSION.md
* PERFORMANCE_BASELINES.md

These documents evolved alongside the codebase and describe the engineering philosophy, architectural decisions, testing strategy, and roadmap.

---

# Current Status

**Phase 4 — AI Narrative Layer**

Milestone 11f complete. The deterministic platform is production-ready; optional Executive Narrative generation is available when enabled.

Completed capabilities include:

* Deterministic Analytics
* Executive Reasoning
* Executive Reporting
* System Transparency
* Business Narrative Translation Layer
* Executive Narrative (AI-Assisted)
* Behavioural Application Testing
* Golden Dataset Registry
* Golden User Journeys
* Clarification Testing
* Temporal Intelligence
* Dataset Lifecycle Testing
* Engineering Readiness

Enable narrative generation with `OIC_NARRATIVE_ENABLED=true` (see `docs/AI_ENGINEERING/ARCHITECTURE.md`).

---

# Future Direction

Phase 5 introduces an LLM evaluation framework.

The AI narrative layer:

* communicates deterministic findings
* applies registry-driven business translation before executive presentation
* remains fully governed by deterministic evidence
* preserves explainability and transparency

This project demonstrates how Large Language Models can be integrated into trustworthy analytical systems without compromising engineering discipline.

---

# Portfolio Purpose

This repository forms part of my transition from Data Engineering into AI Engineering.

Its objective is to demonstrate not only AI capability, but the engineering practices required to build maintainable, explainable, production-quality AI systems.
