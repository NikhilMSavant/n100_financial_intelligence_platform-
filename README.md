# Nifty 100 Financial Intelligence Platform

A 12-module financial analytics platform built on 92 Nifty 100 companies: ETL →
50+ KPI ratio engine → investment screener → peer comparison → valuation →
cash-flow intelligence → NLP pros/cons → PDF reporting → KMeans clustering →
Streamlit dashboard → FastAPI REST layer.

Built against the actual uploaded datasets (`companies.xlsx`, `profitandloss.xlsx`,
`balancesheet.xlsx`, `cashflow.xlsx`, `analysis.xlsx`, `documents.xlsx`,
`prosandcons.xlsx`, plus the 5 supplementary files) — every number in `output/`
and `reports/` was computed from that real data, not mocked.

## Honest build notes

This sandbox has **no network access**, so `fastapi`, `uvicorn`, `streamlit`,
`plotly`, and `pytest` could not be `pip install`ed here:

- The **Streamlit dashboard** (`src/dashboard/`) and **FastAPI server**
  (`src/api/`) are delivered as complete, correct, ready-to-run source code,
  written and reviewed against the spec — but were not executed live in this
  environment. Everything they depend on (the screener engine, ratio engine,
  peer engine) *was* executed and unit-tested directly.
- Radar charts use **matplotlib** instead of Plotly (Plotly isn't installed
  offline); the dashboard source itself uses Plotly per spec, since the
  person running it will have a normal internet connection.
- The 100 ETL/KPI/DQ unit tests were run with a small stdlib-only test
  runner (`tests/run_tests.py`) standing in for `pytest`, since `pytest`
  wasn't installable either. The 10 API tests are written in real pytest +
  `TestClient` style (`tests/api/test_api.py`) and will run once you
  `pip install fastapi uvicorn httpx pytest` in an environment with network
  access.
- Two real bugs were found and fixed during the build (both are visible in
  the git history / prior commits if you're following along): a capital
  allocation sign-classification bug where missing cash-flow snapshots
  defaulted to "-" instead of being excluded, and a KMeans clustering
  distortion caused by two companies (BEL, HAL) with near-zero equity
  producing >4,000% ROE, fixed via P5/P95 winsorisation.
- Several of the spec's illustrative "expected company count" ranges for
  screener presets don't match this dataset's actual valuation multiples
  (median P/E ≈46x here vs. the spec's assumption of ≈20x) — documented in
  `docs/analyst_guide.pdf` section 2 rather than silently adjusted.

## Setup

```bash
pip install -r requirements.txt
```

## Run order

```bash
python src/etl/loader.py                          # Sprint 1: build nifty100.db
python src/analytics/populate_ratios.py            # Sprint 2: financial_ratios table
python src/screener/export.py                      # Sprint 3: screener_output.xlsx
python src/analytics/peer_reports.py                # Sprint 3: peer_comparison.xlsx + radar charts
python src/analytics/valuation.py                   # Sprint 4: valuation_summary.xlsx
python src/nlp/parser.py                            # Sprint 5: analysis_parsed.csv
python src/nlp/pros_cons_generator.py                # Sprint 5: pros_cons_generated.csv
python src/analytics/cashflow_intelligence.py        # Sprint 5: cashflow_intelligence.xlsx
python src/reports/tearsheet.py                     # Sprint 5: 92 tearsheet PDFs
python src/reports/sector_report.py                  # Sprint 5: sector + portfolio PDFs
python src/analytics/clustering.py                   # Sprint 6: cluster_labels.csv + charts
python src/reports/analyst_guide.py                  # Sprint 6: analyst_guide.pdf
python src/reports/acceptance_checklist.py            # Sprint 6: acceptance_checklist.pdf
python tests/run_tests.py tests/etl tests/kpi tests/dq # Sprint 6: pytest_report.html

streamlit run src/dashboard/app.py    # dashboard: http://localhost:8501
uvicorn src.api.main:app --port 8000  # API: http://localhost:8000/docs
```

## Project structure

```
data/nifty100.db          SQLite database (12 tables)
data/raw/                  7 core Excel files (as uploaded)
data/supporting/            5 supplementary Excel files
db/schema.sql              10-table SQLite schema with FK constraints
src/etl/                   loader.py, validator.py (16 DQ rules), normaliser.py
src/analytics/             ratios.py, cagr.py, cashflow_kpis.py, scoring.py,
                            populate_ratios.py, peer.py, peer_reports.py,
                            valuation.py, cashflow_intelligence.py, clustering.py
src/screener/               engine.py, export.py
src/nlp/                    parser.py, pros_cons_generator.py
src/reports/                 tearsheet.py, sector_report.py, analyst_guide.py,
                            acceptance_checklist.py
src/dashboard/               app.py, pages/01-08, utils/db.py
src/api/                    main.py, deps.py, routers/ (8 files, 16 endpoints)
src/qa/                     acceptance_gates.py
config/screener_config.yaml All threshold definitions, analyst-editable
tests/                      etl/, kpi/, dq/, api/ + run_tests.py
notebooks/                  exploratory_queries.sql
output/                     All CSV/XLSX deliverables
reports/                    tearsheets/, sector/, portfolio/, radar_charts/,
                            elbow_plot.png, correlation_heatmap.png, pytest_report.html
docs/                       analyst_guide.pdf, acceptance_checklist.pdf
```

## Test results

100/100 ETL + KPI + DQ unit tests pass (`reports/pytest_report.html`).
20/20 acceptance gates pass (`docs/acceptance_checklist.pdf`).
