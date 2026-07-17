# Nifty 100 Financial Intelligence Platform — Sprint 1 (Data Foundation)

This is a **working, tested** Sprint 1 deliverable — not a template. Every script
here has been run end-to-end against your real 12 Excel files, and the numbers
below are actual output, not projections.

## What's in this zip

```
data/raw/                  7 core Excel files (companies, profitandloss, balancesheet,
                            cashflow, analysis, documents, prosandcons)
data/supplementary/        5 supplementary Excel files (sectors, stock_prices,
                            market_cap, financial_ratios, peer_groups)
src/etl/normaliser.py      normalize_year() + normalize_ticker() (Day 2)
tests/etl/test_normaliser.py  35 unit tests, all passing (Day 2)
db/schema.sql              12-table SQLite schema, PK/FK, indexes (Day 4)
src/etl/loader.py           Loads all 12 files -> db/nifty100.db (Day 4-5)
src/etl/validator.py        All 16 DQ rules -> output/validation_failures.csv (Day 3)
notebooks/exploratory_queries.sql   10 queries, all verified to run (Day 7)
requirements.txt, .env(.template), Makefile
```

## How to run it

```powershell
pip install -r requirements.txt
python src/etl/loader.py       # builds db/nifty100.db
python src/etl/validator.py    # writes output/validation_failures.csv
python -m pytest tests/ -v     # 35 unit tests
```

## Real results from running this against your data

**Load audit** (`output/load_audit.csv`):

| Table | Source rows | Loaded | Rejected | Notes |
|---|---|---|---|---|
| companies | 92 | 92 | 0 | |
| profitandloss | 1,276 | 1,164 | 112 | dup PKs + 8 orphan tickers |
| balancesheet | 1,312 | 1,140 | 172 | dup PKs + orphan tickers |
| cashflow | 1,187 | 1,056 | 131 | dup PKs + orphan tickers |
| analysis | 20 | 16 | 4 | orphan tickers |
| documents | 1,585 | 1,457 | 128 | orphan tickers |
| prosandcons | 16 | 14 | 2 | orphan tickers |
| sectors | 92 | 92 | 0 | |
| stock_prices | 5,520 | 5,520 | 0 | |
| market_cap | 552 | 552 | 0 | |
| financial_ratios | 1,184 | 1,041 | 143 | dup PKs + orphan tickers |
| peer_groups | 56 | 56 | 0 | |

`PRAGMA foreign_key_check` → **0 violations** ✅ (exit criteria met)

**Data-quality findings** (`output/validation_failures.csv`): 881 total (3 CRITICAL, 878 WARNING)
across all 16 DQ rules. Full breakdown by rule is printed when you run `validator.py`.

## Three real issues this build found and handled (read before Day 6 manual review)

1. **`output/duplicate_pk_rows.csv` — 259 rows.** Several companies (e.g. `ASIANPAINT`,
   `ADANIPORTS`) have exact-duplicate rows in the raw Excel files — same company, same
   year, repeated. The loader keeps the first occurrence and quarantines the rest; every
   quarantined row is listed in this file with its source `id` so you can trace it back.

2. **`output/fk_orphan_companies.csv` — 9 tickers.** `ULTRACEMCO`, `UNIONBANK`,
   `UNITDSPR`, `VBL`, `VEDL`, `WIPRO`, `ZOMATO`, `ZYDUSLIFE` (and one more) have
   transaction data (P&L, balance sheet, etc.) but **no entry in `companies.xlsx`**
   (which only has 92 rows, not 100). This is why row counts don't hit the full
   expected totals — it's a genuine gap in the source data, not a loader bug. Worth
   raising with whoever owns `companies.xlsx`.

3. **`documents.xlsx` column name bug** — the source column is `Annual_Report`
   (capitalized), not `annual_report`. Found because the DQ-13 URL check flagged
   1,457 "malformed" URLs that were actually just NULL from a silent rename mismatch.
   Fixed in the loader; leaving this note here so nobody re-introduces it.

## Design decisions worth knowing about

- **`normalize_year()`** treats bare years (e.g. `"2013"`) as fiscal-year-end March
  (`"2013-03"`), matching Indian fiscal year convention. `"TTM"` is kept as a literal
  sentinel string, not converted to a date — it's excluded from year-based joins.
- **`analysis` table is NOT one row per company.** Each company has up to 4 rows
  (10-year / 5-year / 3-year / TTM growth figures), which the original schema
  assumption got wrong until this was checked directly against the data.
- 12 source files map 1:1 to 12 tables (not 10 — the ticket text says 10 but the
  actual file/table count is 12; `financial_ratios` and `market_cap` are separate
  tables from `analysis`).

## What's NOT done yet (Sprint 2+)

- Ratio Engine (computing `financial_ratios` from raw statements, vs. the
  supplementary file which is pre-computed reference data)
- Peer benchmarking, screener, dashboard, API — later sprints per the project doc

## If you want to keep going

Read `output/duplicate_pk_rows.csv` and `output/fk_orphan_companies.csv` first —
that's the real Day 6 manual-review work, already narrowed down for you instead of
you having to hunt for it across 12 files.
