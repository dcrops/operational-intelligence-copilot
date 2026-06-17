# Technical Debt Log

Tracked limitations, known gaps, and planned future enhancements for the Operational Intelligence Copilot.

---

## Temporal Intelligence / Date Constraint Handling

**Status:** Planned

### Context

Manual testing identified that questions containing date or period constraints are currently analysed across the full dataset.

**Example question:**  
"How has performance changed for April 2026?"

**Current behaviour:**  
The system analyses the full available dataset (e.g. January to June 2026).

**Problem:**  
The user asked for a specific period, but temporal constraints are not currently extracted or applied. This can produce misleading answers.

### Desired future behaviour

The system should detect temporal constraints in user questions and either:

- filter the dataset before analysis, or
- explicitly warn that temporal filtering is not yet supported.

### Examples to support in future

- April 2026
- March
- Q1 2026
- Q2
- this month
- last month
- compare April to May
- since March
- after April

### Suggested future milestone

**Milestone 8 — Temporal Intelligence**

**Potential phased approach:**

| Phase | Scope |
|-------|--------|
| Phase 1 | Explicit months, years, quarters |
| Phase 2 | Relative periods |
| Phase 3 | Comparative periods |
