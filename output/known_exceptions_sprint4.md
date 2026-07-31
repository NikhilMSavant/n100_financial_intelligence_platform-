# Sprint 4 known exceptions and deviations

## company_name data quality issue (Day 23)
- 17 companies had extra content after an embedded newline character in
  their company_name field. Most were just a trailing "\n"; two
  (APOLLOHOSP, ASIANPAINT) had an actual company description leaked into
  the name field from the source Excel file (e.g. "Asian Paints\nIndian
  Multi-National Paint and Coating Manufacturing Company").
- Fixed in db.py's get_companies() by taking only the text before the
  first newline - applies globally to every dashboard screen that uses
  this function, not just the Company Profile page where it was found.
  
## CSV download scope fix (Day 24)
- Spec: "CSV download button generates well-formed CSV with all visible
  columns." Initial implementation exported the full 24-column internal
  dataframe, not just the 6 columns actually shown in the on-screen
  table. Fixed to export result[display_cols] instead of the full
  result dataframe.


## Capital Allocation Map company count (Day 25)
- Treemap shows 91 of 92 companies. ATGL (Adani Total Gas Ltd) has zero
  rows in the cashflow table - a genuine pre-existing data gap, not
  introduced by this screen. Confirmed via direct query
  (SELECT * FROM cashflow WHERE company_id = 'ATGL' -> 0 rows).
- Handled with a visible caption note on the screen itself explaining the
  gap, rather than silently showing 91 with no explanation.

## Annual Reports live-check false negative (Day 25)
- BSE's servers return 403 Forbidden to HTTP requests without a
  browser-like User-Agent header - confirmed by direct testing (same
  URL: 403 without header, 200 with one). Without this fix, the live
  "Check links for availability" feature incorrectly flagged every
  genuinely working BSE report URL as "Report unavailable."
- Fixed by adding a standard browser User-Agent to the request headers
  in is_url_reachable(). Verified against TCS: 13 real report years now
  correctly show as available, only the 2 genuine data gaps (2009-03,
  2010-03, where the source data literally contains the string "Null")
  show the unavailable badge.

## Multiple pros/cons rows per company (Day 27 QA)
- prosandcons table can have more than one row per company (e.g. INFY has
  2 rows with different pros/cons text) - Company Profile's pros/cons
  section originally used .iloc[0], silently dropping any additional
  rows. Fixed to combine text from all rows for a company. Found during
  systematic 10-ticker QA testing across sectors.

## Day 27 Integration QA summary
- Tested 10 tickers across 5 sectors (IT: HCLTECH/INFY, Financials:
  AXISBANK/BAJAJFINSV, Consumer Staples: BRITANNIA/DABUR, Energy:
  ADANIENSOL/ADANIGREEN, Healthcare: APOLLOHOSP/CIPLA) against all core
  data functions - no crashes.
- Found and fixed: Company Profile's pros/cons section only showed the
  first prosandcons row per company; INFY has 2 rows (4 total items),
  only 2 were shown. Fixed to combine all rows.
- Confirmed no company has zero rows in financial_ratios or
  profitandloss (the two most critical tables) - the worst cases are
  ATGL (no cashflow, documented Day 25) and JIOFIN/ADANIGREEN (short
  history, handled gracefully throughout).
- Screener slider extremes tested: all-permissive -> 66/92 companies
  (some drop due to genuinely missing data in one of the 10 filtered
  metrics); all-restrictive -> 0 companies, clean empty table, CSV
  download still works without error.
- Chart sizing verified responsive at narrower browser widths (tested
  on Trend Analysis, our most complex multi-axis chart).
- Company Profile load time: backend data queries measured at 7-26ms
  for 5 tickers (TCS, RELIANCE, HDFCBANK, INFY, ASIANPAINT), and real
  browser page loads confirmed well under the 3-second requirement.

## Sprint 4 cross-verification (post-Day-28 review)
Went back through the Sprint 4 spec line-by-line before starting Sprint 5,
same rigor as Sprint 3's cross-verification. Found and fixed 4 issues:

1. **Sector donut chart "11 sectors" claim** - spec says 11, actual data
   has exactly 10 distinct broad_sector values. Same spec/reality count
   mismatch pattern seen elsewhere in the project (likely conflating the
   11 peer groups with broad sectors, which are different groupings).
   The chart correctly shows all 10 real sectors; not a bug to fix.

2. **Company Profile card missing sector/sub-sector/NSE ticker** - spec
   explicitly lists these; only name and description were shown. Fixed
   to display all 5 required fields.

3. **ROE/ROCE chart was single-axis, not "dual-axis"** as spec explicitly
   requires. Fixed to give ROE and ROCE independently-scaled, color-coded
   axes (matching the same approach used in Trend Analysis).

4. **Screener results table missing company_name and sector columns** -
   spec explicitly lists these. Fixed to merge them in from get_companies()
   and get_sectors() (reusing the Day 23 name-cleaning fix, not a raw
   duplicate query) for both the table display and the CSV export.

## Real data quality bug found: ABB / Abbott India name swap
- companies.xlsx has ticker ABB (ABB India Ltd - industrial automation,
  subsidiary of Switzerland's ABB Ltd) mapped to "Abbott India Ltd"'s
  name and description (an unrelated pharmaceutical company). Confirmed
  via web search and cross-checked against the about_company text, which
  unambiguously describes Abbott's pharma business, not ABB's automation
  business.
- Verified this affects DISPLAY ONLY: searched every file referencing
  company_name and confirmed none use it for filtering, joining, or
  computation - every calculation throughout all 4 sprints has correctly
  used company_id (ticker) as the key. ABB's financial data, ratios,
  screener results, peer rankings, and valuation flag have always been
  correct; only the human-readable label was wrong.
- Fixed permanently in loader.py via a COMPANY_NAME_CORRECTIONS dict
  applied immediately after the companies table loads, so the correction
  survives every future run_pipeline.py execution rather than being
  silently reverted by the next reload from the raw (still-wrong)
  companies.xlsx source file.