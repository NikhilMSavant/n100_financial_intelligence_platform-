# Sprint 2 Retrospective — Financial Ratio Engine

## Formula decisions
- ROE denominator uses (equity_capital + reserves) as net worth; ROE returns None (not 0)
  when net worth <= 0, since the ratio is economically undefined for negative equity.
- Debt-to-Equity intentionally returns 0.0 (not None) when borrowings = 0, so debt-free
  companies sort correctly in the screener rather than being dropped as missing data.
- ICR = None is treated as "Debt Free" via a separate `icr_label` column rather than an
  infinite value, so downstream numeric aggregation (averages, percentiles) doesn't need
  special-casing infinity.
- CAGR: 6 edge cases are stored as an explicit flag column alongside a NULL value, so a
  screener or dashboard can distinguish "no growth data" from "growth is undefined because
  the company swung from profit to loss" (DECLINE_TO_LOSS) etc.
- composite_quality_score in this table is a first-pass P10/P90-winsorised absolute score;
  Sprint 3 recomputes a sector-relative version for the screener export.

## Edge-case log findings (output/ratio_edge_cases.log, 268 lines)
- **OPM mismatches for banks (AXISBANK, BAJFINANCE, etc.)**: the source `opm_percentage`
  field is wildly out of range (values like -10277%) for lenders, because "operating profit"
  in a banking P&L doesn't map to sales the way it does for a manufacturer. Categorised as
  **data source issue** — the ratio engine's computed OPM is used for analytics; the source
  field is not meaningful for Financials-sector companies and is suppressed in the dashboard
  for that sector.
- **ROE/ROCE divergences of 5-20pp** (ADANIENT, BAJAJFINSV, TATAMOTORS, TECHM, etc.):
  categorised as **version difference** — companies.xlsx's `roce_percentage`/`roe_percentage`
  columns appear to be a scrape taken at a different point in time (different fiscal year end)
  than the balance-sheet/P&L history loaded here.
- **TCS ROE**: source value of 0.52% is implausible for a company with 45%+ engine-computed
  ROE across the observation window — categorised as **formula discrepancy** in the source
  (likely a decimal/unit error upstream). Engine value used for analytics; source value is
  display-only, per Day 13 instructions.
- **ADANIGREEN / TRENT ROCE**: diff > 85pp / 21pp — categorised as **data source issue**;
  source ROCE appears to reflect a materially different capital base than the loaded balance
  sheet history.

## financial_ratios row count vs. target
Loaded **1,072** company-year rows (target in the sprint brief was 1,100+). This is a real
data-driven number, not a shortfall in the engine: 92 companies × up to 12 fiscal years would
be 1,104 at full coverage; the small gap comes from companies with genuinely shorter listed
histories (see DQ-14 in validation_failures.csv) and the one excluded ADANIENSOL shell row.
Decision: report the true count rather than pad it — documented here per Definition of Done's
spirit of "manual spot-check ... difference must be less than 0.1%" (accuracy over volume).

## Unit tests
47/47 KPI formula unit tests pass (tests/kpi/test_ratios.py, test_cagr.py,
test_cashflow_kpis.py) — exceeds the 20-test target in the sprint brief.
