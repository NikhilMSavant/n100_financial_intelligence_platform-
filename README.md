# Nifty 100 Financial Intelligence Platform

An end-to-end financial analytics platform covering 92 Nifty 100 companies:
ETL + data-quality validation, a 40+ KPI ratio/CAGR/cash-flow engine, a
screener + peer-percentile engine, a valuation module, an 8-screen Streamlit
dashboard, an NLP pros/cons generator, and batch PDF report generation.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Run order (Makefile targets)

```bash
make load        # Sprint 1: build nifty100.db from data/raw + data/supplementary
make validate     # Sprint 1: run 16 DQ rules -> output/validation_failures.csv
make ratios       # Sprint 2: populate financial_ratios, capital_allocation.csv
make screener     # Sprint 3: screener_output.xlsx, peer_comparison.xlsx, radar charts
make valuation    # Sprint 4: valuation_summary.xlsx, valuation_flags.csv
make nlp          # Sprint 5: pros_cons_generated.csv, analysis_parsed.csv
make cashflow     # Sprint 5: cashflow_intelligence.xlsx, distress_alerts.csv
make reports      # Sprint 5: 92 tearsheets + 11 sector PDFs + portfolio summary
make test         # run all unit tests (tests/etl, tests/kpi)
make dashboard    # streamlit run src/dashboard/app.py
make clean        # remove generated db/output/reports artifacts
```

Or run the full pipeline end-to-end:

```bash
make all
```

## Dashboard

```bash
streamlit run src/dashboard/app.py
```

Opens on `http://localhost:8501` with 8 screens in the sidebar:

1. **Home** — 6 summary KPI tiles, sector donut chart, top-5 by composite score, year selector.
2. **Company Profile** — search/autocomplete, KPI tiles, 10yr Revenue/PAT bars, ROE/ROCE dual-axis line, pros/cons.
3. **Screener** — 10 sliders + 6 preset buttons, live-updating results table, CSV download.
4. **Peer Comparison** — peer-group dropdown, 8-axis radar vs peer average, side-by-side KPI table with benchmark highlight.
5. **Trend Analysis** — multi-metric (up to 3) 10-year overlay with YoY % annotations.
6. **Sector Analysis** — Revenue/ROE/Market-Cap bubble chart, sector median KPI bars.
7. **Capital Allocation Map** — treemap of the 8 capital-allocation patterns, click-through company list.
8. **Annual Reports** — per-company report archive with live link-health check.

Every screen is defensive against missing/partial company history: metrics
render `N/A` rather than crashing, and an unknown ticker shows
"Ticker not found — please try another".

## Repository layout

```
config/            screener_config.yaml (analyst-editable thresholds)
data/raw/           7 core source workbooks
data/supplementary/ 5 supplementary workbooks
db/                 schema.sql, nifty100.db (generated)
notebooks/          exploratory_queries.sql
output/             all generated CSV/XLSX/log deliverables
reports/            tearsheets/, sector/, portfolio/, radar_charts/
src/etl/            normaliser.py, loader.py, validator.py
src/analytics/      ratios.py, cagr.py, cashflow_kpis.py, populate_ratios.py,
                     peer.py, valuation.py, radar.py, export_peer_comparison.py
src/screener/       engine.py, composite_score.py, export_screener.py
src/nlp/            parser.py, pros_cons_generator.py
src/reports/        tearsheet.py, sector_report.py, portfolio_summary.py
src/dashboard/       app.py, pages/01..08, utils/db.py
tests/etl/, tests/kpi/  unit tests (run via tests/run_tests.py — see note below)
```

## Test runner note

The sandbox this project was originally built in has no outbound network
access, so `pytest` could not be `pip install`-ed. `tests/run_tests.py` is a
small dependency-free collector that runs every `test_*` function in
`tests/etl/` and `tests/kpi/`, including simple generator-based fixtures
(`def conn(): yield sqlite3.connect(...)`). If your environment has `pytest`
available, the same test files run under it unmodified — just `pytest tests/`.

## Known data caveats

See `output/known_exceptions.md` and `output/sprint2_retrospective.md` for a
full account of source-data anomalies encountered (e.g. bank OPM fields,
TCS's implausible source ROE, ADANIENSOL's pre-listing shell row) and how
each was resolved.
