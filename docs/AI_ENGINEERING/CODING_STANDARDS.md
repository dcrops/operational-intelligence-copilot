# Operational Intelligence Copilot

# Coding Standards

**Version:** 1.0
**Last Updated:** June 2026

---

# Purpose

This document defines the coding standards used throughout the Operational Intelligence Copilot.

The objective is to maintain a codebase that is:

* readable
* maintainable
* testable
* reusable
* explainable
* consistent

These standards apply to both human-written and AI-generated code.

---

# General Principles

Code should be written for the next engineer rather than the original author.

Readability is preferred over cleverness.

Simple solutions are preferred over complex solutions when they satisfy the same requirements.

---

# Repository Organisation

The repository is organised into logical engineering areas.

```text
src/
    operational_intelligence/

ui/

tests/

data/

docs/
```

Each area has a clear responsibility.

Avoid mixing UI, business logic and analytics.

---

# Separation of Responsibilities

The project follows strict architectural boundaries.

## Analytics

Responsible for calculations only.

Analytics should never:

* render UI
* produce executive conclusions
* make presentation decisions

---

## Reasoning

Responsible for transforming findings into executive reasoning.

Reasoning should never:

* perform analytical calculations
* contain Streamlit code

---

## Presentation

Responsible for rendering results.

Presentation should never:

* perform business logic
* perform analytics
* create executive reasoning

---

## Testing

Testing should verify behaviour.

Testing code should not contain production logic.

---

# Module Design

Each module should have a single responsibility.

Prefer:

```
TrendAnalysisTool
```

over:

```
AnalyticsManager
```

Large "manager" classes should generally be avoided.

---

# Function Design

Functions should:

* perform one task
* have descriptive names
* minimise side effects
* return predictable results

Avoid excessively long functions.

If a function becomes difficult to understand, consider extracting smaller helpers.

---

# Class Design

Classes should represent cohesive concepts.

Avoid "god objects" responsible for many unrelated behaviours.

Prefer composition over inheritance where practical.

---

# Naming Conventions

Names should describe intent.

Examples:

Good:

* DatasetProfiler
* ExecutiveReasoningEngine
* TrendAnalysisTool
* OperationalAssessment

Avoid vague names such as:

* Manager
* Helper
* Utils
* Stuff

unless the responsibility genuinely matches.

---

# Reuse

Before adding new code:

1. Search for an existing implementation.
2. Determine whether it can be extended.
3. Refactor if appropriate.
4. Create new code only when necessary.

Do not duplicate functionality.

---

# Configuration

Avoid hard-coded values.

Configuration should be centralised where practical.

Magic numbers and unexplained constants should be avoided.

---

# Type Hints

Use Python type hints consistently.

Public APIs should always include explicit types.

Example:

```python
def analyse(
    dataset: pd.DataFrame,
    metric: str,
) -> ToolResult:
```

---

# Pydantic Models

Structured data exchanged between components should use Pydantic models where appropriate.

Models should validate important constraints.

Validation should occur as close to the source as practical.

---

# Error Handling

Errors should be:

* explicit
* informative
* actionable

Avoid silently swallowing exceptions.

Unexpected failures should fail clearly.

---

# Documentation

Public classes and functions should include concise docstrings.

Complex behaviour should be explained.

Avoid comments that merely repeat the code.

Document *why*, not *what*.

---

# Testing Standards

Every new capability should be accompanied by appropriate tests.

The preferred testing order is:

1. Unit tests
2. Integration tests
3. Application tests

Tests should focus on behaviour rather than implementation details.

---

# Application Tests

Application tests should:

* represent realistic user journeys
* verify visible behaviour
* avoid brittle UI assertions
* reuse helper functions
* use Golden Datasets
* use Golden Scenarios

---

# Refactoring

Refactoring is encouraged when it improves:

* readability
* maintainability
* reuse

Do not refactor solely for stylistic preference.

Refactoring should provide measurable engineering value.

---

# AI-Generated Code

All AI-generated code must be reviewed before acceptance.

Review should consider:

* correctness
* maintainability
* readability
* architecture
* testing
* duplication

AI-generated code should never be committed without human review.

---

# Git Strategy

Development follows small, meaningful commits.

Each commit should represent a complete engineering milestone wherever practical.

Commit messages should describe engineering intent rather than implementation detail.

Example:

```
Implement executive reasoning orchestration
```

Preferred over:

```
Fixed bug
```

---

# Definition of Done

A feature is considered complete when:

* implementation is complete
* tests pass
* architecture has been reviewed
* documentation has been updated where required
* code has been reviewed
* a meaningful Git commit has been created

---

# Future Evolution

These coding standards should evolve alongside the project.

When introducing new patterns:

* update this document
* maintain consistency
* avoid conflicting conventions

The objective is continuous improvement rather than rigid adherence to historical decisions.

---

# Related Documentation

This document should be read alongside:

* ENGINEERING_HANDBOOK.md
* ARCHITECTURE.md
* ROADMAP.md
* AI_COLLABORATION.md

Together these documents form the Operational Intelligence Copilot Engineering Knowledge Base.
