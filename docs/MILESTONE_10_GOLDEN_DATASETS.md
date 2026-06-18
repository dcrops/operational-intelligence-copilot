# Milestone 10b — Golden Dataset Registry

This document registers the canonical sample datasets under `data/sample/`. These files are long-lived regression assets for Streamlit AppTest, Playwright smoke tests, regression testing, future LLM evaluation, demos, and portfolio documentation.

**Status:** Milestone 10b (documentation only). No datasets, code, or tests were modified to produce this registry.

---

## Repository layout (current)

```
data/sample/
├── education_demo.csv          # Primary golden — education domain
├── manufacturing_demo.csv      # Primary golden — manufacturing domain
├── workforce_demo_v2.csv       # Primary golden — workforce domain (app-loaded)
├── workforce_demo.csv          # Legacy / tiny smoke dataset
└── trend_volatility_test.csv   # Secondary regression — trend volatility
```

**App integration today:** The Streamlit sidebar loads three samples via `ui/components/upload.py`:

| Sidebar label        | File                     | Internal dataset name |
|----------------------|--------------------------|------------------------|
| Workforce demo       | `workforce_demo_v2.csv`  | `workforce_demo`       |
| Manufacturing demo   | `manufacturing_demo.csv` | `manufacturing_demo`   |
| Education demo       | `education_demo.csv`     | `education_demo`       |

`workforce_demo.csv` and `trend_volatility_test.csv` are committed regression assets but are **not** wired into the app sidebar yet. They are intended for upload-based AppTest scenarios and targeted regression.

**Regeneration scripts** (deterministic, seed `42` where noted):

| Dataset               | Generator script                          |
|-----------------------|-------------------------------------------|
| `education_demo.csv`  | `scripts/generate_education_demo.py`      |
| `manufacturing_demo.csv` | `scripts/generate_manufacturing_demo.py` |
| `workforce_demo_v2.csv`  | `scripts/generate_workforce_demo_v2.py`  |

`workforce_demo.csv` and `trend_volatility_test.csv` have no generator scripts in the repository. Treat them as hand-maintained minimal fixtures unless a generator is added in a future milestone.

### Future organisation (documentation only — do not move files now)

If the sample library grows, a future option is:

```
data/sample/
├── golden/          # Primary and secondary regression CSVs
├── legacy/          # Tiny smoke fixtures
└── README.md        # Pointer to this document
```

No file moves are required for Milestone 10b. Existing paths remain stable for Git history, scripts, and tests.

---

## Golden dataset philosophy

Golden datasets in this project are:

- **Deterministic** — fixed seeds and committed CSVs produce repeatable analytical outcomes.
- **Committed to Git** — they are version-controlled regression assets, not generated at test runtime.
- **Stable over time** — changes require explicit review; regenerated files must be diffed and expectation tests updated.
- **Intentionally small** — human-readable row counts (roughly 250–300 rows for primary datasets; fewer for targeted fixtures).
- **Human-readable** — column names and values support demos and portfolio walkthroughs.
- **Suitable for demos** — three domain stories (workforce, manufacturing, education) cover the product narrative.
- **Suitable for regression testing** — each dataset encodes known analytical scenarios.

**Policy:** Do not create new datasets unless an existing dataset cannot exercise a required scenario. Synthetic DataFrames built inline in `tests/support/factories.py` remain appropriate for isolated unit and integration tests only; they are not substitutes for golden CSV regression.

---

## Dataset registry

### 1. `manufacturing_demo.csv`

| Field | Detail |
|-------|--------|
| **Dataset name** | `manufacturing_demo` |
| **Domain** | Manufacturing / production operations |
| **Role** | **Primary golden dataset** |
| **Rows / columns** | 300 rows; `month`, `production_line`, `shift`, `defects`, `downtime_minutes`, `units_produced`, `site`, `supervisor` |
| **Purpose** | Canonical manufacturing demo and the broadest golden asset for pipeline, temporal, snapshot, variance, trend, and executive-reasoning regression |

**Primary analytical capabilities covered**

| Capability | Coverage |
|------------|----------|
| Trend | ✓ Rising `downtime_minutes` by month; trend questions on defects and downtime |
| Variance | ✓ `production_line` comparisons; highest/lowest defects; dual top/bottom questions |
| Anomaly | ✓ Injected high-defect and high-downtime records (deterministic seed) |
| Temporal filtering | ✓ `month` column; April 2026, Q1 2026, and full-series questions |
| Snapshot intelligence | ✓ Single-month questions (e.g. April 2026) activate snapshot mode |
| Snapshot contributors | ✓ `production_line` dimension supports contributor highest/lowest |
| Clarification | ✓ Ambiguous performance questions require metric selection |
| Executive reasoning | ✓ Multi-finding runs (e.g. defects + risk) populate assessment, conclusions, actions |
| Transparency | ✓ Auto-resolved metric, dimension, aggregation, and temporal trails |

**Representative user questions**

- Which production line has the highest defects?
- Which production line has the highest and lowest defects?
- How has downtime changed over time?
- How has defects changed in April 2026?
- How has performance changed over time? *(expects metric clarification)*
- Which production line has the highest defects and what is the risk?
- What looks unusual and what should I investigate?
- Analyse this dataset

**Expected stable outcomes**

- **Variance (defects by line):** Line A and Line B remain low-defect baselines; non–A/B lines carry higher defect totals; injected high-defect rows (45–80) appear on selected records.
- **Trend (downtime):** Month-over-month downtime totals increase (designed upward trend in generator).
- **Temporal / snapshot:** April 2026 questions filter to a single month and activate snapshot findings rather than multi-period trend.
- **Clarification:** “How has performance changed over time?” returns a metric clarification with all profile metrics as options.
- **Executive reasoning:** High-severity variance findings can produce Critical assessment, themed conclusions, and priority actions on broad/risk questions.
- **Anomaly:** Injected high-downtime rows (120–200 minutes) and high-defect rows support anomaly detection routes.

**Known edge cases**

- Multiple dimensions (`shift`, `site`, `supervisor`) can affect ambiguity if questions reference non-primary dimensions.
- Dual comparison questions must not trigger comparison-direction clarification when top and bottom are requested together.
- Snapshot vs trend routing depends on temporal bucket count (single month → snapshot; Q1 → trend with three periods).
- Regenerating the CSV changes injected row indices but preserves statistical storylines when using seed `42`.

**Notes for future maintenance**

- Prefer editing `scripts/generate_manufacturing_demo.py` and regenerating rather than hand-editing CSV cells.
- Lock golden expectations in AppTest (Milestone 10c+) using variance targets, snapshot activation, and executive-reasoning section visibility.
- Primary candidate for Playwright smoke: load sidebar sample → ask highest-defects question → assert Direct Answer and Analytical Findings.

---

### 2. `education_demo.csv`

| Field | Detail |
|-------|--------|
| **Dataset name** | `education_demo` |
| **Domain** | Education / schools |
| **Role** | **Primary golden dataset** |
| **Rows / columns** | 300 rows; `month`, `school`, `year_level`, `attendance_rate`, `behaviour_incidents`, `average_score`, `campus`, `program_type` |
| **Purpose** | Education-domain demo; mean-aggregation trend and variance; clarification and attendance-rate semantics |

**Primary analytical capabilities covered**

| Capability | Coverage |
|------------|----------|
| Trend | ✓ School C attendance decline over months; attendance rate uses **mean** aggregation |
| Variance | ✓ School-level behaviour incidents and attendance comparisons |
| Anomaly | ◐ Injected low-attendance and high-behaviour rows (secondary to trend/variance story) |
| Temporal filtering | ✓ Monthly series across six months |
| Snapshot intelligence | ◐ Single-month attendance questions |
| Snapshot contributors | ◐ `school` dimension available for contributor analysis |
| Clarification | ✓ Ambiguous performance and “best class” questions require metric clarification |
| Executive reasoning | ◐ Supported on multi-finding / broad analysis runs |
| Transparency | ✓ Metric inference and aggregation trails (mean for rates) |

**Representative user questions**

- How has attendance changed over time?
- Which school has the highest behaviour incidents?
- Which school has the lowest attendance?
- Which class is performing best? *(metric clarification)*
- How has performance changed? *(metric clarification)*
- What looks unusual and what should I investigate?
- Analyse this dataset

**Expected stable outcomes**

- **Trend (attendance_rate):** Mean aggregation; period values remain plausible percentages (0–100).
- **Variance:** School B dominates total behaviour incidents; lowest attendance targets align with injected low-attendance scenarios (excluding School C’s intentional decline narrative).
- **School C storyline:** Attendance declines from ~92% toward ~75% across months (generator-designed trend).
- **Clarification:** Vague performance questions surface metric clarification listing all potential metrics.

**Known edge cases**

- `year_level` wording (“class”) routes to variance but still requires metric clarification.
- Multiple schools × campuses × year levels create dense grouping; questions must name the intended metric.
- Rate metrics must not be sum-aggregated in trend evidence.

**Notes for future maintenance**

- Regenerate via `scripts/generate_education_demo.py` (seed `42`).
- Use for AppTest clarification journeys (scenarios G–I in the Milestone 10 test plan).
- Pair with manufacturing for cross-domain semantic regression (`tests/test_cross_dataset_semantics.py` already parametrizes this file for clarification smoke).

---

### 3. `workforce_demo_v2.csv`

| Field | Detail |
|-------|--------|
| **Dataset name** | `workforce_demo` *(internal name when loaded in app)* |
| **Domain** | Workforce / HR operations |
| **Role** | **Primary golden dataset** |
| **Rows / columns** | 250 rows; `employee_id`, `employee_name`, `department`, `month`, `hours`, `overtime_hours`, `absence_days`, `location`, `manager`, `employment_type` |
| **Purpose** | Workforce demo in the app; trend, variance, anomaly, and multi-metric clarification scenarios |

**Primary analytical capabilities covered**

| Capability | Coverage |
|------------|----------|
| Trend | ✓ Ops `hours` increase Jan→May; Finance remains lowest-hours department |
| Variance | ✓ Department-level hours comparisons |
| Anomaly | ✓ Five hour spikes (600–1000) in HR/Sales/IT; high overtime and absence injections |
| Temporal filtering | ✓ Five monthly periods |
| Snapshot intelligence | ◐ Single-month workforce questions |
| Snapshot contributors | ◐ `department` dimension |
| Clarification | ✓ Ambiguous performance questions require metric selection across four metrics |
| Executive reasoning | ◐ Multi-route analysis and risk-style questions |
| Transparency | ✓ Multi-metric profiles and inference trails |

**Representative user questions**

- Which department has the highest hours?
- How have hours changed over time?
- How has overtime changed over time?
- What looks unusual and what should I investigate?
- How has performance changed? *(metric clarification)*
- Analyse this dataset

**Expected stable outcomes**

- **Variance:** Ops records highest total hours; Finance lowest among departments.
- **Trend:** Ops hours increase gradually by month index in generator design.
- **Anomaly:** Exactly five hour anomalies (600–1000), five high-overtime rows (>50), five high-absence rows (≥10) when regenerated with seed `42`.
- **Clarification:** Performance ambiguity offers four metrics: `hours`, `overtime_hours`, `absence_days`, plus employee-level dimensions as profiled.

**Known edge cases**

- Anomalies deliberately avoid Ops/Finance rows to preserve trend/variance narratives.
- Employee-grain data can produce large evidence lists; UI caps evidence display separately.
- App maps file `workforce_demo_v2.csv` to dataset name `workforce_demo` — document this alias in tests.

**Notes for future maintenance**

- Regenerate via `scripts/generate_workforce_demo_v2.py` (seed `42`).
- Primary workforce golden asset; superseded `workforce_demo.csv` for comprehensive scenarios.
- Use for AppTest anomaly and multi-metric clarification flows.

---

### 4. `workforce_demo.csv`

| Field | Detail |
|-------|--------|
| **Dataset name** | `workforce_demo` *(if uploaded by filename)* |
| **Domain** | Workforce (minimal) |
| **Role** | **Legacy / tiny smoke dataset** |
| **Rows / columns** | 4 rows; `month`, `department`, `hours` |
| **Purpose** | Fast upload smoke, minimal CSV parsing, and lightweight clarification/variance checks without loading 250-row fixtures |

**Primary analytical capabilities covered**

| Capability | Coverage |
|------------|----------|
| Trend | ◐ Four months — insufficient for robust trend classification |
| Variance | ✓ Ops April spike (1000 hours) vs HR/Finance |
| Anomaly | — Not designed for anomaly injection |
| Temporal filtering | ◐ Minimal month coverage |
| Snapshot intelligence | — |
| Snapshot contributors | — |
| Clarification | ◐ Only one metric column — limited ambiguity surface |
| Executive reasoning | ◐ Only if findings are produced |
| Transparency | ◐ Minimal inference trails |

**Representative user questions**

- Which department has the highest hours?
- Upload CSV smoke test *(engineering)*

**Expected stable outcomes**

- Ops row in April 2026 dominates total hours.
- Dataset loads instantly; suitable for “CSV upload succeeded” assertions only.

**Known edge cases**

- Too small for trend volatility, snapshot, or executive-reasoning golden expectations.
- Not loaded by the app sidebar; must be uploaded manually in AppTest.

**Notes for future maintenance**

- Retain for upload smoke only; do not expand into a primary golden dataset.
- If a scenario needs workforce analytics, use `workforce_demo_v2.csv`.

---

### 5. `trend_volatility_test.csv`

| Field | Detail |
|-------|--------|
| **Dataset name** | `trend_volatility_test` *(stem if uploaded)* |
| **Domain** | Synthetic time series (domain-agnostic) |
| **Role** | **Secondary regression dataset** |
| **Rows / columns** | 5 rows; `month`, `hours` |
| **Purpose** | Isolate **volatile** trend classification (alternating 100 / 500) without confounding dimensions or variance stories |

**Primary analytical capabilities covered**

| Capability | Coverage |
|------------|----------|
| Trend | ✓ **Primary focus** — volatile label expected for alternating series |
| Variance | — Single metric, no groups |
| Anomaly | — |
| Temporal filtering | ◐ Optional single-month filters |
| Snapshot intelligence | — |
| Snapshot contributors | — |
| Clarification | — Single metric |
| Executive reasoning | ◐ Only if trend finding severity triggers reasoning |
| Transparency | ◐ Minimal |

**Representative user questions**

- How have hours changed over time?
- How has hours volatility changed over time?

**Expected stable outcomes**

- Trend analysis classifies the series as **volatile** (large step changes between 100 and 500).
- No metric clarification required (`hours` is the only metric).

**Known edge cases**

- Not representative of real operational data — intentional oscillation.
- Not integrated into sidebar samples; AppTest must upload explicitly.
- Unsuitable for demo narratives; use only in regression.

**Notes for future maintenance**

- Do not merge into `workforce_demo_v2.csv`; volatility must remain isolated.
- Add AppTest golden expectation for trend label in Milestone 10e (volatile trend scenario).
- Consider a tiny generator script if the series ever needs regeneration.

---

## Regression capability matrix

Legend: **Yes** = strong, intended coverage · **Partial** = possible but not primary · **—** = not applicable · **Planned** = upcoming Milestone 10c+ AppTest/Playwright (not yet implemented)

| Dataset | Trend | Variance | Anomaly | Temporal | Snapshot | Snapshot Contributors | Clarification | Executive Reasoning | Transparency | AppTest | Playwright Smoke |
|---------|:-----:|:--------:|:-------:|:--------:|:--------:|:---------------------:|:-------------:|:-------------------:|:------------:|:-------:|:----------------:|
| `manufacturing_demo.csv` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Planned | Planned |
| `education_demo.csv` | Yes | Yes | Partial | Yes | Partial | Partial | Yes | Partial | Yes | Planned | Planned |
| `workforce_demo_v2.csv` | Yes | Yes | Yes | Yes | Partial | Partial | Yes | Partial | Yes | Planned | Planned |
| `workforce_demo.csv` | Partial | Yes | — | Partial | — | — | Partial | Partial | Partial | Planned | Planned |
| `trend_volatility_test.csv` | Yes | — | — | Partial | — | — | — | Partial | Partial | Planned | — |

### Recommended AppTest / Playwright assignments (Milestone 10c+)

| Scenario type | Preferred golden dataset |
|---------------|---------------------------|
| Sidebar bootstrap + sample load | `manufacturing_demo.csv` |
| Variance happy path | `manufacturing_demo.csv` |
| Trend + mean rate semantics | `education_demo.csv` |
| Clarification journeys | `education_demo.csv`, `workforce_demo_v2.csv` |
| Temporal + snapshot | `manufacturing_demo.csv` |
| Snapshot contributors | `manufacturing_demo.csv` |
| Anomaly + multi-metric | `workforce_demo_v2.csv` |
| CSV upload smoke | `workforce_demo.csv` |
| Volatile trend label | `trend_volatility_test.csv` |
| Executive Reasoning UI | `manufacturing_demo.csv` (multi-finding + risk question) |
| Transparency contract | Any primary golden dataset |

---

## Relationship to existing tests

Today, golden CSV files are referenced directly in a small set of pytest modules (for example `tests/conftest.py` fixtures and `tests/test_cross_dataset_semantics.py` E2E clarification parametrisation). Most behavioural coverage still uses **synthetic factories** in `tests/support/factories.py`, which mirror but do not replace these CSVs.

Milestone 10c and beyond should:

1. Add golden expectation registries keyed by dataset name and question.
2. Prefer these committed CSVs for AppTest and Playwright over inline synthetic DataFrames.
3. Treat changes to golden CSVs as breaking changes requiring expectation updates.

---

## Definition of Done (Milestone 10b)

- [x] `docs/MILESTONE_10_GOLDEN_DATASETS.md` created
- [x] Every existing dataset under `data/sample/` documented
- [x] Canonical dataset roles clarified (primary / secondary / legacy)
- [x] Regression capability matrix included
- [x] No code, data, or test changes

**Next milestone:** 10c — Golden expectation registry and Streamlit AppTest infrastructure.
