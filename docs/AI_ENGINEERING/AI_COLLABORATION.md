# Operational Intelligence Copilot

# AI Collaboration Guide

**Version:** 1.0
**Last Updated:** June 2026

---

# Purpose

This document describes how AI tools are used during the development of the Operational Intelligence Copilot.

The objective is not to replace software engineering with AI.

The objective is to combine human engineering judgement with AI-assisted development to produce higher-quality software.

This document serves as the standard operating procedure for collaboration between the human engineer, ChatGPT, Cursor, and future AI development tools.

---

# Guiding Philosophy

AI is treated as an engineering partner, not an autonomous developer.

Human judgement remains responsible for:

* Architecture
* Engineering decisions
* Trade-off analysis
* Testing
* Product direction
* Final approval

AI accelerates implementation, documentation, review, and learning.

---

# Roles and Responsibilities

## Human Engineer

The human engineer owns the project.

Responsibilities include:

* Defining project goals
* Approving architecture
* Making engineering decisions
* Reviewing AI-generated code
* Running tests
* Committing code
* Learning and understanding the implementation

The human engineer remains accountable for all code committed to the repository.

---

## ChatGPT

ChatGPT acts as a Senior AI Engineering Advisor.

Primary responsibilities include:

* Architecture design
* Milestone planning
* Engineering reviews
* Trade-off analysis
* Code critique
* Testing strategy
* Documentation
* Project planning
* Explaining engineering concepts
* Challenging assumptions

ChatGPT should prioritise engineering quality over implementation speed.

It should critically review proposed solutions rather than automatically accepting them.

---

## Cursor

Cursor is responsible for implementation.

It is used in two distinct modes.

### PLAN Mode

PLAN Mode is used before implementation.

Objectives include:

* Reviewing proposed architecture
* Planning implementation
* Identifying affected files
* Estimating scope
* Highlighting risks

No code should be written until the plan has been reviewed.

---

### AGENT Mode

AGENT Mode performs implementation.

Typical responsibilities include:

* Writing production code
* Refactoring
* Creating tests
* Updating documentation
* Applying agreed architectural changes

Each Agent task should implement only a single milestone wherever practical.

---

# Standard Development Workflow

Every feature follows the same engineering workflow.

```text
Idea

↓

Architecture Discussion (ChatGPT)

↓

Milestone Definition

↓

Cursor PLAN Mode

↓

Human Review

↓

Cursor AGENT Mode

↓

Implementation

↓

Human Review

↓

Testing

↓

Architecture Review

↓

Git Commit

↓

Update Documentation

↓

Next Milestone
```

This workflow intentionally favours small, incremental progress over large, difficult-to-review changes.

---

# Milestone Strategy

Every milestone should:

* Have a single responsibility
* Be independently reviewable
* Be independently testable
* Produce a meaningful Git commit

Large architectural changes should be broken into multiple milestones.

Examples:

Instead of:

> Build Executive Reasoning

The work was divided into:

* Executive Themes
* Operational Assessment
* Executive Conclusions
* Priority Actions
* Integration

This approach improves review quality and reduces implementation risk.

---

# Code Review Process

AI-generated code is never assumed to be correct.

Every milestone should be reviewed before acceptance.

Reviews should consider:

* Architecture
* Maintainability
* Readability
* Reusability
* Testability
* Future extensibility

The goal is to improve engineering quality rather than simply confirm correctness.

---

# Testing Workflow

Testing is performed continuously throughout development.

Typical workflow:

1. Unit tests
2. Integration tests
3. Streamlit AppTests
4. Manual application review
5. Full regression suite
6. Git commit

Application behaviour is verified before new development begins.

---

# Learning Philosophy

This project is intentionally treated as an AI Engineering apprenticeship.

The objective is not simply to build software.

The objective is to understand:

* Why architectural decisions were made
* Why one design is preferable to another
* Engineering trade-offs
* Production-quality practices
* Modern AI Engineering workflows

Where appropriate:

* ask questions
* request explanations
* challenge assumptions
* review alternatives

Understanding is considered more valuable than rapid implementation.

---

# Engineering Principles

Throughout development, the following principles should be maintained:

* Deterministic reasoning before LLM reasoning
* Evidence before conclusions
* Infrastructure before features
* Reuse before duplication
* Architecture before implementation
* Behaviour over implementation details
* Small milestones
* Continuous testing
* Continuous review

---

# Documentation Workflow

Documentation evolves alongside the codebase.

Major architectural changes should update:

* Engineering Handbook
* Architecture
* Roadmap

where appropriate.

Documentation is considered part of the deliverable rather than an afterthought.

---

# AI Tool Evolution

The project currently uses:

* ChatGPT
* Cursor

Future tools (such as Codex or other AI engineering assistants) may be incorporated if they provide measurable improvements in quality, productivity, or review capability.

New tools should complement the existing workflow rather than replace engineering judgement.

---

# Definition of Success

AI collaboration is considered successful when it results in:

* Better engineering decisions
* Cleaner architecture
* Improved documentation
* Higher-quality testing
* Increased understanding
* Faster implementation without sacrificing maintainability

Success is measured by engineering quality rather than the amount of AI-generated code.

---

# Related Documentation

This guide should be read alongside:

* ENGINEERING_HANDBOOK.md
* ARCHITECTURE.md
* ROADMAP.md

Together these documents describe the engineering philosophy, system architecture, project roadmap, and AI-assisted development workflow for the Operational Intelligence Copilot.
