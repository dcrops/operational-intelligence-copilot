# AI Collaboration Guide

**Project:** Operational Intelligence Copilot

**Purpose:** Define the engineering workflow used when collaborating with AI assistants throughout the project.

This document is part of the Engineering Knowledge Base and should evolve alongside the codebase.

---

# Philosophy

This project is an AI Engineering apprenticeship rather than simply an application.

The objective is not only to build software, but also to demonstrate professional engineering practices suitable for an AI Engineering portfolio.

AI assistants are treated as engineering collaborators rather than autonomous code generators.

Engineering judgement always remains the responsibility of the human engineer.

---

# Primary Engineering Principles

Throughout the project we prioritise:

* maintainability over cleverness
* readability over brevity
* deterministic behaviour over hidden magic
* reusable infrastructure over duplication
* engineering discipline over rapid feature delivery

The objective is to build software that another engineer could confidently maintain.

---

# Engineering Knowledge Base

The Engineering Knowledge Base is the authoritative source of truth for the project.

It currently consists of:

* ENGINEERING_HANDBOOK.md
* ARCHITECTURE.md
* ROADMAP.md
* CODING_STANDARDS.md
* REGRESSION.md
* PERFORMANCE_BASELINES.md
* PHASE_3_ENGINEERING_REVIEW.md
* AI_COLLABORATION.md

If previous conversation context conflicts with these documents, the Engineering Knowledge Base takes precedence.

These documents are living documents and should evolve alongside the implementation.

---

# Engineering Workflow

Development follows a disciplined engineering workflow.

1. Discuss architecture.

2. Challenge assumptions.

3. Design a milestone.

4. Create an implementation plan.

5. Review the plan.

6. Use Cursor PLAN Mode.

7. Review the PLAN.

8. Use Cursor AGENT Mode.

9. Review implementation.

10. Execute automated testing.

11. Perform manual validation where appropriate.

12. Review engineering outcomes.

13. Commit to Git.

14. Update engineering documentation.

Engineering decisions should be made before implementation whenever practical.

---

# Roles

## ChatGPT

Primary responsibilities:

* architecture guidance
* engineering reviews
* trade-off analysis
* milestone design
* documentation
* engineering education
* portfolio strategy
* challenging assumptions

ChatGPT reviews implementation but does not automatically approve design decisions.

---

## Cursor

Primary responsibilities:

* implementation
* repository analysis
* PLAN Mode
* AGENT Mode
* repository-wide engineering review
* code generation
* refactoring within approved scope

Cursor is responsible for implementation rather than architectural direction.

---

## Human Engineer

Final responsibility always remains with the project owner.

Responsibilities include:

* approving architecture
* accepting or rejecting recommendations
* validating behaviour
* deciding milestone scope
* maintaining engineering quality

AI recommendations are considered inputs rather than requirements.

---

# Milestone Philosophy

Milestones should remain intentionally small.

Each milestone should:

* have one responsibility
* be independently reviewable
* be independently testable
* produce a meaningful Git commit
* improve the engineering quality of the project

Avoid combining unrelated work into a single milestone.

---

# Review Process

Every milestone should include:

* implementation review
* automated testing
* manual validation (where appropriate)
* Git review
* documentation review

Major project phases should additionally include:

* repository-wide engineering review
* architecture review
* engineering readiness assessment

The completion of Phase 3 established this as the standard approach for future major phases.

---

# Testing Philosophy

The project prioritises behavioural confidence over implementation detail.

Testing strategy includes:

* unit tests
* integration tests
* behavioural Streamlit AppTests
* Golden Dataset Registry
* Golden Scenario Registry
* manual smoke testing
* regression execution

Behavioural tests should validate user-visible outcomes rather than implementation details.

Regression execution is documented in:

* REGRESSION.md

Performance reference measurements are documented in:

* PERFORMANCE_BASELINES.md

---

# Documentation Philosophy

Documentation is treated as part of the software.

Engineering documentation should remain synchronised with implementation.

Changes affecting architecture, engineering workflow or development practices should update the relevant engineering documents as part of the same milestone whenever practical.

---

# Architecture First

Before implementation, engineering discussions should focus on:

* architectural boundaries
* engineering trade-offs
* maintainability
* future extensibility
* testing implications

Implementation should follow architecture rather than drive it.

---

# AI Integration Philosophy

The project deliberately separates deterministic reasoning from probabilistic AI.

Deterministic systems establish analytical facts.

Future AI capabilities communicate those facts.

This distinction preserves:

* explainability
* governance
* engineering confidence
* regression stability

Future AI integration should extend the platform rather than replace deterministic reasoning.

---

# Phase 4 Guidance — AI Narrative Layer

Phase 4 work follows a **boundary-first** approach:

1. Define the narrative contract before enabling real LLM calls.
2. Preserve the deterministic pipeline — routing, clarification, analytics, and report generation remain unchanged.
3. Narrative code consumes completed deterministic output only; it must not mutate findings, routes, clarification, direct answers, or executive report sections.
4. Do not wire legacy `llm_answer_generator.py` into new Phase 4 paths; use the narrative boundary under `src/operational_intelligence/llm/`.
5. Milestone 11a introduces the boundary and `DeterministicNarrativeGenerator` only — no OpenAI integration, prompts, or UI narrative rendering until later milestones.
6. Milestone 11b introduces `PromptArtifact` — use a **PromptArtifact-first** workflow: `NarrativeRequest` → `PromptArtifactBuilder` → `PromptArtifact` → `NarrativeGenerator`. Evidence assembly belongs in `PromptArtifactBuilder`, not in `NarrativeRequest`.
7. Do not wire legacy `prompts.py` into the narrative path; it predates `PromptArtifact`.

### Milestone 11c — OpenAI integration principles

1. OpenAI code lives in provider adapters only (`OpenAINarrativeGenerator`, `OpenAIPromptFormatter`, `OpenAIClient`).
2. Mock at the `LLMClient` boundary in tests — not at the OpenAI SDK boundary.
3. Fallback must be explicit in `NarrativeResponse.limitations`, not silent.
4. Deterministic analytics remain authoritative; LLM output is optional communication on `AnalysisResult.narrative` only.

### Milestone 11d — UI rendering principles

1. AI-assisted narrative must not replace Direct Answer, Executive Reasoning, or System Transparency.
2. Always show governance caption when narrative renders.
3. Presentation logic belongs in `ui/narrative_presentation.py` — no LLM calls from UI components.
4. Limitations must remain visible (not hidden in expanders).

---

# Continuous Improvement

Engineering processes should evolve as the project matures.

If a workflow proves beneficial during development, it should be incorporated into this document so future collaboration remains consistent.

The Engineering Knowledge Base should accurately describe how the project is engineered at every stage of its evolution.
