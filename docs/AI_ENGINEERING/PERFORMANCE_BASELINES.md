# Performance Baselines

**Version:** 1.0  
**Last Updated:** June 2026  
**Milestone:** 10h — Engineering Readiness & Regression

This document records **indicative local timings** for major user and engineering workflows. These numbers are reference points for future comparison — not service-level objectives, not CI gates, and not optimisation targets.

---

## Measurement environment

| Property | Value |
|----------|-------|
| **Date recorded** | June 2026 |
| **Machine** | Local Windows development workstation |
| **Operating system** | Windows 10 (build 26200) |
| **Python** | 3.13.5 |
| **pandas** | 3.0.3 |
| **Dataset** | `data/sample/manufacturing_demo.csv` (300 rows) unless noted |

Timings vary by hardware, CPU load, and Python/Streamlit versions. Treat values below as **order-of-magnitude references**, not pass/fail thresholds.

---

## Workflow baselines

| Workflow | Description | Observed time |
|----------|-------------|---------------|
| Application launch | `launch_app()` — Streamlit AppTest bootstrap | ~0.17 s |
| Dataset load | `pd.read_csv()` on manufacturing demo | ~0.01 s |
| Dataset profiling | `DatasetProfiler().profile_dataframe()` | ~0.01 s |
| Analysis execution | `run_analysis()` resolved variance question | ~0.003 s |
| Executive report generation | Included in analysis path (report + direct answer) | Included in analysis row |
| Complete AppTest journey | `run_golden_scenario("manufacturing_bootstrap_smoke")` — load sample, analyse, render report sections | ~0.06 s |

---

## What these baselines cover

### Application launch

Streamlit AppTest initialises `app.py` in-process. This baseline reflects cold-start cost of the testing harness, not a production deployment.

### Dataset loading

Reading a committed golden CSV from disk. Upload and sidebar sample paths both ultimately call `pd.read_csv()`.

### Dataset profiling

Domain-agnostic column detection, metric/dimension inference, and suitable-tool selection via `DatasetProfiler`.

### Analysis execution

Full path through `run_analysis()` including intent routing, pipeline execution, answer generation, and executive report assembly for a resolved manufacturing question:

> Which production line has the highest defects?

### Executive report generation

Not measured separately — it is part of the analysis execution baseline. The analysis outcome includes `direct_answer`, `findings`, and `report`.

### Complete AppTest journey

End-to-end behavioural test path: sidebar sample load, question entry, analysis submission, and results rendering for the manufacturing bootstrap smoke scenario.

---

## How to use these baselines

1. **Regression investigation** — If a workflow becomes noticeably slower after a change, compare against these references locally.
2. **Phase 4 planning** — LLM integration will add latency; these deterministic baselines establish the pre-LLM floor.
3. **Do not** use these values as automated test assertions — Milestone 10h documents timings only.

---

## Re-measurement

Re-record this document when:

- Hardware or OS changes materially
- Major dependency upgrades occur (Python, pandas, Streamlit)
- A milestone significantly changes the analysis pipeline or AppTest harness

To re-measure locally, run representative operations with `time.perf_counter()` around the workflows listed above.

---

## Related documentation

- [REGRESSION.md](REGRESSION.md) — regression execution tiers
- [ENGINEERING_HANDBOOK.md](ENGINEERING_HANDBOOK.md) — engineering philosophy
