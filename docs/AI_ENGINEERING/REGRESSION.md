# Regression Execution Guide

**Version:** 1.1  
**Last Updated:** June 2026  
**Project Status:** MVP Complete (Milestone 14)

This document is the canonical guide for running the Operational Intelligence Copilot regression suite. It describes the three execution tiers established during Phase 3 and extended through Milestone 13g. The full suite comprises **595 tests** including **11 AppTest modules**.

---

## Purpose

The regression suite protects the deterministic analytics platform and Streamlit application behaviour. Tests verify **behaviour**, not exact rendered text or internal implementation details. At MVP closure, all tiers pass with zero failures required for ship.

---

## Three regression tiers

### Tier 1 — Targeted milestone / feature testing

Use when working on a specific application area or milestone file.

```bash
python -m pytest tests/app/test_<area>.py -m app -q
```

**Examples:**

```bash
python -m pytest tests/app/test_golden_journeys.py -m app -q
python -m pytest tests/app/test_clarification_journeys.py -m app -q
python -m pytest tests/app/test_temporal_snapshot_journeys.py -m app -q
python -m pytest tests/app/test_dataset_lifecycle_journeys.py -m app -q
python -m pytest tests/test_prompt_construction.py -q
python -m pytest tests/test_business_narrative_translation.py -q
python -m pytest tests/test_executive_context_builder.py -q
python -m pytest tests/test_executive_advisor_narrative.py -q
python -m pytest tests/test_narrative_boundary.py -q
python -m pytest tests/test_openai_narrative_generator.py -q
python -m pytest tests/test_narrative_presentation.py -q
python -m pytest tests/app/test_narrative_rendering.py -m app -q
python -m pytest tests/app/test_follow_up_question_buttons.py -m app -q
python -m pytest tests/app/test_follow_up_workflow.py -m app -q
python -m pytest tests/test_follow_up_reliability.py -q
```

**When to use:** After changing helpers, golden scenarios, a single AppTest module, prompt artifact models, narrative generator protocol, or Business Narrative Translation Layer rules.

**Expected result:** All tests in the targeted file pass with zero failures.

---

### Tier 2 — Application behavioural regression

Use when changes may affect Streamlit application behaviour broadly.

```bash
python -m pytest -m app -q
```

**When to use:** After modifying `app.py`, UI components, analysis service wiring, session state, or shared AppTest helpers.

**Expected result:** All AppTests pass (11 modules at MVP closure).

---

### Tier 3 — Full deterministic regression

Use before declaring a milestone complete, before Phase transitions, or before significant merges.

```bash
python -m pytest -q
```

**When to use:** Final validation for any milestone; MVP release check; periodic full-suite verification.

**Expected result:** Full suite passes with zero failures. Warnings from Streamlit deprecation notices may appear; profiling date-inference warnings should not recur after the Milestone 10h profiling fix.

---

## Pass criteria

| Criterion | Requirement |
|-----------|-------------|
| Failures | Zero |
| App exceptions | None during AppTest runs |
| Determinism | Same inputs produce same outcomes (committed golden CSVs) |
| External services | Not required |
| API keys / `.env` | Not required |

---

## AppTest prerequisites

- Python environment with dependencies from `requirements-dev.txt` installed (includes `requirements.txt` and `pytest`)
- `streamlit` with AppTest support (`streamlit.testing.v1`)
- Project root as working directory (or `pythonpath = .` via `pytest.ini`)
- No running Streamlit server required — AppTest launches the script in-process

AppTests load sample datasets from the sidebar or upload committed CSV fixtures. No network access is required.

---

## Golden Dataset philosophy

Canonical regression assets live under `data/sample/`. See [MILESTONE_10_GOLDEN_DATASETS.md](../MILESTONE_10_GOLDEN_DATASETS.md) for the full registry.

Principles:

- **Deterministic** — fixed committed CSVs, not generated at test runtime
- **Behaviour-focused** — AppTests assert sections, workflows, and transparency markers
- **Reuse** — scenarios registered in `tests/app/golden_expectations.py`

Lifecycle fixtures (e.g. `data/sample/fixtures/empty.csv`) are minimal committed files used only for rejection/recovery scenarios.

---

## AppTest inventory

Phase 3 established core journey modules (below). Phase 5 added results tabs, information architecture, narrative rendering, and follow-up workflow modules — **11 AppTest modules** at MVP closure.

| Module | Journeys | Milestone |
|--------|----------|-----------|
| `tests/app/test_app_bootstrap.py` | Bootstrap smoke, sample load | 10c |
| `tests/app/test_golden_journeys.py` | Manufacturing analysis, education snapshot, workforce clarification | 10d |
| `tests/app/test_clarification_journeys.py` | Metric, dimension, clarification recovery | 10e |
| `tests/app/test_temporal_snapshot_journeys.py` | Temporal filter, snapshot analysis, snapshot contributors | 10f |
| `tests/app/test_dataset_lifecycle_journeys.py` | Onboarding, replacement, invalid recovery | 10g |
| `tests/app/test_results_tabs.py` | Summary / Findings / Audit tabs | 13d |
| `tests/app/test_results_information_architecture.py` | Executive surface hierarchy | 13b |
| `tests/app/test_narrative_rendering.py` | Narrative presentation | 11 |
| `tests/app/test_follow_up_question_buttons.py` | Ask this follow-up buttons | 13g |
| `tests/app/test_follow_up_workflow.py` | Follow-up navigation workflow | 13g |
| `tests/app/test_progressive_disclosure.py` | Legacy disclosure alias | 13c |

Shared infrastructure:

- `tests/app/helpers.py` — AppTest helpers
- `tests/app/golden_expectations.py` — scenario registry
- `tests/app/conftest.py` — `app` fixture

---

## Pre-commit checklist

Before committing Phase 3 application or test changes:

1. Run **Tier 1** for the module you changed
2. If helpers or golden registry changed, run **Tier 2**
3. Confirm zero failures

---

## Pre-MVP-release checklist

Before declaring MVP ship (Milestone 14):

1. Run **Tier 3** — full `python -m pytest -q` (595 tests at MVP closure)
2. Confirm all AppTests pass via **Tier 2**
3. Review [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md) for reference timings
4. Confirm engineering documentation is synchronised (Handbook, Architecture, Roadmap, Milestone 14 review)
5. Confirm no open **Must Fix Before MVP** items in [TECHNICAL_DEBT.md](../TECHNICAL_DEBT.md)

---

## Pre-Phase-4 checklist (historical)

Before beginning Phase 4 (LLM Narrative Generation):

1. Run **Tier 3** — full `python -m pytest -q`
2. Confirm all AppTests pass via **Tier 2** (11 modules at MVP closure)
3. Review [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md) for reference timings
4. Confirm engineering documentation is synchronised (Handbook, Architecture, Roadmap)
5. Confirm no open regression failures in Technical Debt for implemented capabilities

---

## CI readiness

The project is structured for future continuous integration without requiring CI to be implemented in Milestone 10h.

| Property | Status |
|----------|--------|
| Deterministic execution | Yes — no randomness in golden paths |
| External services | None required |
| API keys | None required |
| `.env` files | None required |
| Network | Not required for tests |
| Environment variables | Optional — narrative tests may set `OIC_NARRATIVE_ENABLED=1` and `OIC_NARRATIVE_PROVIDER`; default suite runs with narrative disabled. Real OpenAI verification is manual/dev only — automated regression does not require `OPENAI_API_KEY`. |
| Repeatable install (app) | `pip install -r requirements.txt` |
| Repeatable install (tests) | `pip install -r requirements-dev.txt` |
| Entry command | `python -m pytest -q` |
| Test count at MVP | 595 (full suite) |

**Deferred intentionally:** GitHub Actions workflows, Playwright browser tests, coverage gates, matrix builds.

When CI is added, Tier 2 and Tier 3 commands are sufficient for a minimal pipeline.

---

## Related documentation

- [ENGINEERING_HANDBOOK.md](ENGINEERING_HANDBOOK.md) — testing philosophy
- [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md) — indicative workflow timings
- [MILESTONE_10_GOLDEN_DATASETS.md](../MILESTONE_10_GOLDEN_DATASETS.md) — dataset registry
