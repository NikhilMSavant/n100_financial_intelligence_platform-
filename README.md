# Nifty 100 Financial Intelligence Platform

A working, tested financial data platform covering ETL, ratio analysis,
screening, peer comparison, and an interactive dashboard for all 92
Nifty 100 constituent companies. Built across 4 sprints (Days 1-28);
every deliverable listed below has actually been run against the real
source data, not just described.

## Quick start

```powershell
pip install -r requirements.txt
python run_pipeline.py              # builds/refreshes everything: DB, ratios,
                                     # peer rankings, screener output, valuation
python -m pytest tests/ -v          # 143 unit tests
python -m streamlit run src/dashboard/app.py   # launches the dashboard
```

Use `python -m streamlit run ...` rather than the bare `streamlit run ...`
command — the bare command's launcher script can end up with a stale
hard-coded path if the project folder is ever moved.

**Important:** `run_pipeline.py` must be run any time the schema or ETL
logic changes. `loader.py` rebuilds every table (including `financial_ratios`)
straight from the raw source Excel files, which silently wipes out every
column computed by later steps (CAGR, composite score, ROCE, valuation,
etc.) unless the rest of the pipeline is re-run immediately after. Running
`run_pipeline.py` end-to-end avoids this entirely.

## Project structure

```
data/raw/                  7 core Excel files
data/supplementary/        5 supplementary Excel files
db/schema.sql              12-table SQLite schema
db/nifty100.db             built database (generated, not checked in)
src/etl/                   loader.py, validator.py, normaliser.py (Sprint 1)
src/analytics/              ratios.py, cagr.py, cashflow_kpis.py, peer.py,
                            radar.py, valuation.py, populate_ratios.py (Sprint 2-4)
src/screener/               engine.py, composite_score.py, export_screener.py (Sprint 3)
src/dashboard/               app.py, pages/ (8 screens), utils/db.py (Sprint 4)
config/screener_config.yaml  analyst-editable filter thresholds
tests/                       143 unit tests across etl/ and kpi/
output/                      all generated reports, logs, and known-exceptions docs
reports/radar_charts/        92 PNG radar charts
```

## Sprint 1 — Data Foundation

Loads all 12 source Excel files into a validated SQLite database.

- `db/nifty100.db` — 12 tables, 92 companies, 0 FK violations
- `output/load_audit.csv` — per-table row counts and rejections
- `output/validation_failures.csv` — 16 DQ rules, 881 findings (3 CRITICAL,
  all individually investigated and explained)
- `output/duplicate_pk_rows.csv`, `output/fk_orphan_companies.csv` — real
  data-quality gaps found and quarantined, not silently dropped

**Real issues found:** exact-duplicate rows in several companies' raw
data (ASIANPAINT, ADANIPORTS, etc.), 9 tickers with transaction data but
no entry in `companies.xlsx`, a `documents.xlsx` column name mismatch
(`Annual_Report` vs `annual_report`) that silently nulled 1,457 rows
until caught by a DQ check.

## Sprint 2 — Financial Ratio Engine

Computes 50+ KPIs (profitability, leverage, efficiency, CAGR, cash flow
quality, capital allocation patterns) for every company-year.

- `financial_ratios` table — 1,164 rows, 17 KPI columns
- `output/capital_allocation.csv` — 8-pattern classification per company-year
- `output/ratio_edge_cases.log` — 52 anomalies cross-checked against
  `companies.xlsx`'s pre-computed reference values, each categorized as a
  data source issue or a version/timing difference

**Real issues found:** a `None`-vs-`NaN` handling gap in the CAGR/ratio
functions that crashed on real data with missing fields; a hardcoded-zero
bug that left `interest_coverage` 100% null; a TTM-row exclusion bug that
caused the row count to fall short of the sprint's target.

## Sprint 3 — Screener & Peer Comparison Engine

6 preset stock screeners, peer percentile rankings across 11 industry
groups, and a composite quality score.

- `output/screener_output.xlsx` — 6 preset sheets, color-coded, sorted by
  composite score
- `output/peer_comparison.xlsx` — 11 peer group sheets, percentile
  color-coded, benchmark row highlighted
- `peer_percentiles` table — 596 rows across 11 groups x 10 metrics
- `reports/radar_charts/` — 92 PNGs, one per company

**Real issues found:** two presets (Value Pick, Debt-Free Blue Chip)
needed documented threshold adjustments after investigation showed the
literal spec thresholds returned too few companies against the real
Nifty 100 universe; the composite score needed sector-relative
normalization (not just universe-wide) to satisfy the spec properly; a
recurring stale-data bug class (fixed permanently via `run_pipeline.py`).

## Sprint 4 — Dashboard & Valuation Module

An 8-screen Streamlit dashboard, plus a valuation module.

**Run it:** `python -m streamlit run src/dashboard/app.py`, then open
`http://localhost:8501`.

### Screens

1. **Home** — 6 KPI tiles, sector donut chart, top-5 companies table, year selector
2. **Company Profile** — search, company card, KPI tiles, Revenue/Profit
   and ROE/ROCE charts, pros/cons badges
3. **Screener** — 10 filter sliders (each with an explicit enable
   checkbox), 6 preset buttons, live results table, CSV export
4. **Peer Comparison** — peer group dropdown, radar chart vs. peer
   average, benchmark-highlighted KPI table
5. **Trend Analysis** — up to 3 overlaid metrics, each on its own
   independently-scaled axis, with YoY % change annotations
6. **Sector Analysis** — Revenue/ROE/MarketCap bubble chart, sector
   median KPI bar chart
7. **Capital Allocation Map** — treemap of 91/92 companies by pattern
   (ATGL has no cash flow data in the source files), dropdown filter
8. **Annual Reports** — clickable BSE PDF links per year, with an
   optional live-availability check

### Valuation module

- `output/valuation_summary.xlsx` — 92 companies: P/E, P/B, EV/EBITDA,
  FCF yield, 5-year median P/E, sector-relative overvaluation flag
- `output/valuation_flags.csv` — 44 companies flagged Caution or Discount

**Real issues found:** `company_name` had embedded newlines and, in two
cases, leaked description text; the Home screen's top-5 table needed the
same known-bad-ROE sanitization as the composite score; a missing
`st.plotly_chart()` call silently produced an empty chart section; Plotly
auto-interpreted fiscal-year strings as calendar dates; two non-obvious
Streamlit `session_state` bugs in the screener sliders; BSE returns 403
Forbidden without a browser-like `User-Agent` header, causing every
working report link to be falsely flagged unavailable; the pros/cons
section only showed the first of multiple database rows per company.

## Known limitations and documented deviations

Every deviation from a literal spec requirement — threshold changes,
data quality workarounds, spec/reality count mismatches — is documented
with the reasoning behind it, not silently patched over. See:

- `output/known_exceptions_sprint2.md`
- `output/known_exceptions_sprint3.md`
- `output/known_exceptions_sprint4.md`

And the full sprint retrospectives:

- `output/sprint2_retrospective.md`
- `output/sprint3_retrospective.md`
- `output/sprint4_retrospective.md`

## Testing

```powershell
python -m pytest tests/ -v
```

143 tests across `tests/etl/` (normalizer, 16 DQ rules) and `tests/kpi/`
(ratios, CAGR, cash flow KPIs, composite score, peer ranking, screener
engine, radar chart data, peer comparison export, valuation).