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

Only after this deterministic platform is complete will an AI Narrative Layer be introduced.

The LLM will communicate deterministic findings rather than generate them.

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

        ▼

System Transparency
```

The deterministic pipeline remains the single source of analytical truth.

Future AI capabilities will enhance communication rather than replace analytical reasoning.

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

**Phase 3 — Application Quality Engineering**

✅ Complete

Completed capabilities include:

* Deterministic Analytics
* Executive Reasoning
* Executive Reporting
* Behavioural Application Testing
* Golden Dataset Registry
* Golden User Journeys
* Clarification Testing
* Temporal Intelligence
* Dataset Lifecycle Testing
* Engineering Readiness

The deterministic platform is now considered production-ready.

---

# Future Direction

Phase 4 introduces an AI Narrative Layer.

Rather than generating analytical facts, the AI layer will:

* communicate deterministic findings
* improve executive readability
* remain fully governed by deterministic evidence
* preserve explainability and transparency

This project intentionally demonstrates how Large Language Models can be integrated into trustworthy analytical systems without compromising engineering discipline.

---

# Portfolio Purpose

This repository forms part of my transition from Data Engineering into AI Engineering.

Its objective is to demonstrate not only AI capability, but the engineering practices required to build maintainable, explainable, production-quality AI systems.
