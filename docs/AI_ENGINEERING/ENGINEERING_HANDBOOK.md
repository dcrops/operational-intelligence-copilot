# Operational Intelligence Copilot
# Engineering Handbook

**Version:** 1.0  
**Last Updated:** June 2026  
**Project Status:** Active Development  
**Current Milestone:** Current work: 10h — Performance & Regression Testing

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

Completed:

- Dataset Profiling
- Intent Routing
- Clarification Engine
- Trend Analysis
- Variance Analysis
- Anomaly Detection
- Snapshot Intelligence
- Executive Reporting
- Executive Reasoning
- Operational Assessment
- Executive Conclusions
- Priority Actions
- Golden Dataset Registry
- Application Testing Framework

Current work:

Milestone 10d — Golden User Journeys

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

Together these documents form the Operational Intelligence Copilot Engineering Knowledge Base.