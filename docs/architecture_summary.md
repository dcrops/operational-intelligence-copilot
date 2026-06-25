# Operational Intelligence Copilot — Architecture Summary

Deterministic operational analytics pipeline with a Streamlit UI. Natural-language questions are routed to analysis tools, converted into evidence-backed findings, and rendered as executive reports, direct answers, and transparency trails.

---

# System Overview

The codebase separates **core analytics** (`src/operational_intelligence/`) from **presentation concerns** (`ui/`).

The default user path is **fully deterministic**:

- No LLM is required for the Streamlit application.
- All analytical outputs are reproducible.
- An optional LLM layer exists for future integrations but is not used in the primary workflow.

---

# High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│                 Streamlit UI                │
│                                              │
│  app.py                                      │
│  upload.py                                   │
│  clarification_panel.py                      │
│  results_panel.py                            │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│              Analysis Service                │
│                                              │
│  analysis_service.py                         │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│             Operational Pipeline             │
│                                              │
│  Intent Routing                              │
│  Clarification Detection                     │
│  Tool Orchestration                          │
│  Risk Assessment                             │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│                Analysis Tools                │
│                                              │
│  Trend Analysis                              │
│  Variance Analysis                           │
│  Anomaly Detection                           │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│                Finding Layer                 │
│                                              │
│  Evidence Items                              │
│  Findings                                    │
│  Risk Scoring                                │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│              Presentation Layer              │
│                                              │
│  Executive Reports                           │
│  Direct Answers                              │
│  Investigation Suggestions                   │
│  Transparency Trails                         │
│  Business Narrative Translation (optional)   │
│  Executive Narrative (optional)              │
└──────────────────────────────────────────────┘
```

---

# Major Modules

## Entry Point

| Module | Responsibility |
|---------|-----------------|
| `app.py` | Streamlit shell: dataset preview, question input, analysis trigger, clarification vs results routing |
| `requirements.txt` | Runtime dependencies |

---

# Core Analytics (`src/operational_intelligence/`)

| Module | Responsibility |
|---------|-----------------|
| `models.py` | Pydantic domain models |
| `profiling.py` | Dataset profiling and tool suitability |
| `schema_resolution.py` | NL → column mapping |
| `question_semantics.py` | Intent keywords, aggregation inference, causation safeguards |
| `intent_router.py` | Maps questions to tools |
| `ambiguity_detection.py` | Generates clarification requests |
| `pipeline.py` | Central orchestration layer |
| `trend_analysis.py` | Trend analysis with period evidence |
| `variance_analysis.py` | Group comparison analysis |
| `anomaly_detection.py` | Z-score anomaly detection |
| `risk_assessment.py` | Converts tool outputs into findings |
| `reporting.py` | Executive report generation |
| `answer_generator.py` | Deterministic answer generation |
| `llm_answer_generator.py` | Optional LLM rendering layer |
| `llm/` | LLM interfaces, narrative boundary, Business Narrative Translation Layer, executive context |

---

# Milestone 7+ Modules

| Module | Milestone | Responsibility |
|---------|------------|-----------------|
| `investigation_suggestions.py` | 7 | Deterministic investigation guidance |
| `evidence_utils.py` | 7.1 | Shared evidence enrichment utilities |
| `anomaly_direct_answer.py` | 7.2 | Adaptive anomaly direct-answer generation |
| `ui/transparency.py` | 7.1 | Transparency trail formatting |
| `ui/analysis_service.py` | 7.1 | Metrics analysed population |
| `ui/components/results_panel.py` | 7.1 | Transparency and evidence rendering |

---

# UI Layer (`ui/`)

| Module | Responsibility |
|---------|-----------------|
| `models.py` | UI analysis result container |
| `state.py` | Streamlit session state |
| `analysis_service.py` | Pipeline integration point |
| `formatting.py` | UI formatting helpers |
| `anomaly_presentation.py` | Anomaly business copy |
| `variance_presentation.py` | Variance business copy |
| `components/upload.py` | CSV upload and sample loading |
| `components/clarification_panel.py` | Clarification workflows |
| `components/results_panel.py` | Results presentation |

---

# Data Flow

## 1. Dataset Ingestion

```text
CSV Upload
     ↓
DatasetProfiler
     ↓
DatasetProfile
     ↓
Session State
```

Responsibilities:

- Infer metrics
- Infer dimensions
- Infer date columns
- Suggest suitable analysis tools

---

## 2. Question → Findings

```text
User Question
       ↓
AnalysisRequest
       ↓
IntentRouter
       ↓
OperationalPipeline
       ↓
Clarification Detection
       ↓
Tool Execution
       ↓
Risk Assessment
       ↓
Findings
```

Responsibilities:

- Resolve ambiguity
- Route analytical intent
- Execute relevant tools
- Produce evidence-backed findings

---

## 3. Findings → User Output

```text
Findings
    ↓
ExecutiveReportGenerator
    ↓
AnswerGenerator
    ↓
AnalysisResult
    ↓
Results Panel
```

Outputs:

- Direct Answer
- Executive Summary
- Findings
- Evidence
- Transparency Trails
- Metrics Analysed
- Executive Narrative (optional — via Business Narrative Translation Layer)

### Optional narrative path

```text
Executive Reasoning
        ↓
Business Narrative Translation Layer
        ↓
Executive Narrative
        ↓
Presentation
```

Executive Reasoning and System Transparency retain raw deterministic terminology. Executive Narrative consumes translated business language only.

---

# Evidence Model

Every `EvidenceItem` contains:

```text
metric_name
metric_value
description
supporting_context
```

Supporting context can include:

```text
row_index
mean
standard_deviation
z_score
dimension values
trend statistics
aggregation details
```

Evidence is generated **at the tool layer**.

Presentation layers consume evidence but **never recompute analytics**.

---

# Key Extension Points

## Add a New Analysis Tool

1. Create tool returning `ToolResult`
2. Populate `EvidenceItem`
3. Register in `IntentRouter`
4. Wire into `OperationalPipeline`
5. Add risk assessment mapping
6. Add answer generation support
7. Add tests

---

## Extend Question Understanding

Areas:

```text
question_semantics.py
schema_resolution.py
ambiguity_detection.py
```

Examples:

- New intents
- Improved aggregation detection
- Enhanced clarification logic

---

## Extend Answer Presentation

Areas:

```text
answer_generator.py
anomaly_direct_answer.py
ui/*_presentation.py
```

Examples:

- Executive summaries
- Domain-specific wording
- Audience-aware explanations

---

## Extend Investigation Suggestions

Area:

```text
investigation_suggestions.py
```

Examples:

- New investigation patterns
- Capability-aware suggestions
- Guided drill-downs

---

## Extend Transparency

Area:

```text
ui/transparency.py
```

Examples:

- Additional inference trails
- Temporal decision tracking
- Grouping decision tracking

---

## Optional LLM Path

Area:

```text
llm_answer_generator.py
llm/
```

Examples:

- Narrative generation
- Conversational interfaces
- Alternate answer rendering

---

# Test Structure

## Test Philosophy

Testing evolved from:

> "Does the feature work?"

towards:

> "Will future changes accidentally break existing behaviour?"

---

## Test Types

| Marker | Purpose |
|---------|----------|
| `@pytest.mark.unit` | Isolated logic |
| `@pytest.mark.integration` | Cross-module flows |
| `@pytest.mark.e2e` | End-to-end scenarios |

---

## Test Support

| Path | Purpose |
|-------|----------|
| `tests/conftest.py` | Shared fixtures |
| `tests/support/factories.py` | DataFrame factories |
| `tests/support/builders.py` | Synthetic finding builders |
| `tests/support/assertions.py` | Shared assertions |

---

## Coverage Areas

| Tests | Coverage |
|--------|-----------|
| Profiling | Dataset understanding |
| Schema Resolution | NL → column mapping |
| Question Semantics | Intent detection |
| Ambiguity Detection | Clarification gates |
| Analysis Tools | Trend, variance, anomaly |
| Risk Assessment | Severity scoring |
| Executive Reporting | Report generation |
| Answer Generation | Direct answers |
| Guardrails | Causation safeguards |
| Investigation Suggestions | Milestone 7 |
| Transparency | Milestone 7.1 |
| Adaptive Direct Answers | Milestone 7.2 |
| Cross-Dataset Behaviour | Domain agnosticism |
| Regression Suites | Milestones 5–6 |

---

# Current Test Suite

```text
199 tests
```

Run with:

```powershell
$env:PYTHONPATH="."
python -m pytest
```

---

# Milestone Summary

## Milestone 7 — Investigation Assistant

Delivered:

- Deterministic investigation guidance
- Executive report integration
- Investigation-aware reporting

---

## Milestone 7.1 — Evidence & Transparency Hardening

Delivered:

- Evidence enrichment
- Clarification transparency
- Auto-resolution transparency
- Metrics analysed transparency

---

## Milestone 7.2 — Adaptive Direct Answer Summarisation

Delivered:

- Tiered anomaly answers
- Contextual anomaly explanations
- Mean comparisons
- Z-score transparency
- Domain-agnostic contextual labels

---

# Known Technical Debt

Tracked in:

```text
docs/TECHNICAL_DEBT.md
```

Current focus areas:

- Temporal Intelligence (Milestone 8)
- Capability-aware investigation suggestions
- Pipeline ↔ transparency contract protection
- Deterministic answer ↔ transparency alignment
- Metrics analysed UX improvements
- Guided drill-down investigations

---

# Design Principles

## Deterministic First

Analytics should produce reproducible outputs without requiring an LLM.

---

## Domain Agnostic

Behaviour should emerge from profiles and schema resolution rather than hardcoded dataset assumptions.

---

## Evidence Backed

Findings should always be supported by structured evidence.

---

## Separation of Concerns

Detection, orchestration, reporting, answer generation, and presentation should remain independent.

---

## Transparency

Users should understand:

- what was inferred,
- what was selected,
- what evidence supported the outcome.

---

## Guardrails

The system should acknowledge analytical limitations and avoid unsupported causal claims.

---

# Directory Structure

```text
operational-intelligence-copilot/
├── app.py
├── data/sample/
├── docs/
│   ├── TECHNICAL_DEBT.md
│   └── architecture_summary.md
├── scripts/
├── src/operational_intelligence/
│   ├── pipeline.py
│   ├── trend_analysis.py
│   ├── variance_analysis.py
│   ├── anomaly_detection.py
│   ├── answer_generator.py
│   ├── anomaly_direct_answer.py
│   ├── evidence_utils.py
│   ├── investigation_suggestions.py
│   └── llm/
├── tests/
│   ├── conftest.py
│   ├── support/
│   └── test_*.py
└── ui/
    ├── analysis_service.py
    ├── transparency.py
    └── components/
```

---

# Architecture Summary

The Operational Intelligence Copilot has evolved from a collection of analytical tools into a deterministic operational intelligence system capable of:

- identifying issues,
- explaining findings,
- exposing evidence,
- guiding investigations,
- preserving analytical humility,
- maintaining transparency,
- and protecting behaviour through regression testing.

The architecture emphasises **trust, explainability, and maintainability**, reflecting the design principles required for production-oriented AI systems.