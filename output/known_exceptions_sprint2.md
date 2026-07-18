# Sprint 2 known exceptions and gaps

## Capital allocation classifier (Day 11)
- 2 rows (HDFCLIFE, 2013-03 and 2014-03) have null CFO/CFI/CFF values in the
  source cashflow data - labeled "Incomplete Data" rather than guessed at.
  Plausible explanation: early post-listing years for an insurer, which
  often has non-standard cash flow reporting.
- 19 rows fall outside the spec's 8 named patterns:
  - 15 rows are sign combination (-, +, -): CFO negative, CFI positive,
    CFF negative. Not covered by the spec's pattern table. Business reading:
    operating cash shortfall covered by asset sales, while still paying
    down financing obligations.
  - 4 rows involve a zero in one of the three signs (e.g. CFI or CFF
    exactly 0 for the year), which the spec's table doesn't address since
    it's defined only in terms of strict +/- signs.
  These are labeled "Unclassified" rather than forced into a nearby pattern.

## financial_ratios table (Day 12)
- `book_value_per_share` is null for all 1,164 rows. This ratio requires
  shares outstanding, which does not exist in any of the 12 source files
  (verified by inspecting every column across companies.xlsx, profitandloss.xlsx,
  balancesheet.xlsx, and all supplementary files in Sprint 1). Cannot be
  computed without acquiring this data from an external source.
- `composite_quality_score` uses a documented custom formula (not specified
  in the original sprint doc): normalized average of ROE, Debt-to-Equity,
  Interest Coverage, and single-year CFO/PAT ratio, each scaled to 0-100.
  See src/analytics/quality_score.py for the exact thresholds used.

## Bank/Financials sector carve-out (Day 13)
- Spec expects 19 companies in the Financials broad_sector; actual data
  shows 23: AXISBANK, BAJAJFINSV, BAJAJHLDNG, BAJFINANCE, BANKBARODA, CANBK,
  CHOLAFIN, HDFCBANK, HDFCLIFE, ICICIBANK, ICICIGI, ICICIPRULI, INDUSINDBK,
  IRFC, JIOFIN, KOTAKBANK, LICI, PFC, PNB, RECLTD, SBILIFE, SBIN, SHRIRAMFIN.
  Likely explanation: BAJAJHLDNG (a holding company) and/or IRFC/PFC/RECLTD
  (government-owned NBFCs/infrastructure financiers) may not have been
  counted as "Financials" in whatever reference produced the "19" figure -
  classification boundaries for diversified holding companies and public
  sector NBFCs vary by source. The D/E high-leverage carve-out logic itself
  works generically off the broad_sector field regardless of count, so this
  discrepancy doesn't block the carve-out - it's a data/classification note
  only.