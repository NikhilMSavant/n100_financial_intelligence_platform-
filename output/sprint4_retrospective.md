# Sprint 4 Retrospective — Dashboard & Valuation Module

**Sprint dates:** Day 22–28 | **Story points:** 55 SP | **Status:** Complete

## What we built

| Component | Purpose |
|---|---|
| `src/dashboard/app.py` | Streamlit entry point, page config, sidebar navigation |
| `src/dashboard/utils/db.py` | 10 cached (`@st.cache_data(ttl=600)`) data-access functions |
| `src/dashboard/pages/01_home.py` through `08_reports.py` | All 8 required screens |
| `src/analytics/valuation.py` | FCF yield, sector-relative P/E overvaluation flags |
| `output/valuation_summary.xlsx`, `output/valuation_flags.csv` | Valuation deliverables |
| `run_pipeline.py` (extended) | Valuation step added to the guaranteed-order pipeline |

**143 unit tests passing** (132 from Sprints 1-3 + 11 new for the valuation module).

## Key UX and design decisions

- **Streamlit's `pages/` folder must sit next to the script being run**, not at the project root — a genuine structural gotcha found on Day 22 before any screen could even be reached.
- **Sliders alone can't represent "not filtering on a metric."** Every slider has *some* value, so the Screener screen gives each of its 10 sliders an explicit "enable this filter" checkbox — a metric is only applied when its checkbox is checked, rather than every slider always being active at whatever value it happens to show.
- **Multi-metric trend charts need independent y-axes per metric.** Overlaying Revenue (in the hundred-thousands) and ROE (in the tens) on one shared axis flattens the smaller-scale metric to an unreadable line; each selected metric gets its own labeled, color-matched axis instead.
- **Known-bad ROE/ROCE data (BEL, HAL, INDIGO, LT, PNB — confirmed in Sprint 2 Day 13) needed active exclusion in three more places** beyond the composite score: the Home screen's Average ROE tile, the Home screen's top-5 table (with a visible asterisk + caption rather than silent removal), and the Sector Analysis bubble chart (with a caption naming which company was excluded and why).
- **Real click-driven interactivity between a Plotly treemap and a separate Streamlit component isn't natively supported** without extra event-plumbing; the Capital Allocation Map uses a dropdown as a reliable, equally-functional substitute for "click a pattern to see its companies."

## Real bugs found by running against the live app (not just unit tests)

1. **`company_name` data quality issue** — 17 companies had extra content after an embedded newline in the source data; 2 of them (APOLLOHOSP, ASIANPAINT) had an actual company description bleeding into the name field. Fixed at the source in `get_companies()` so every screen benefits.
2. **Top-5 composite score table showed duplicate company-year rows and let known-broken ROE data appear as a "top performer."** Traced to querying Sprint 2's un-sanitized `composite_quality_score` column directly instead of reusing Sprint 3's sector-relative, sanitized scoring pipeline.
3. **A missing `st.plotly_chart()` call** silently produced an entirely empty chart section with no error — the figure was built in memory but never actually rendered. Found while testing a short-history company (JIOFIN) where the missing chart was the only thing visibly wrong.
4. **Plotly auto-interpreted fiscal-year strings as calendar dates**, mislabeling chart x-axes with dates like "Oct 2022" instead of "2023-03". Fixed by explicitly setting `xaxis_type="category"`.
5. **Two Streamlit `session_state` bugs in the Screener**, both non-obvious: (a) all 10 sliders applied simultaneously regardless of relevance to a clicked preset, incorrectly reducing Quality Compounder's correct 21-company result down to 3; (b) once a widget has an explicit `key`, only writing to `st.session_state` — not the widget's `value=` parameter — can change its state on a rerun, so preset button clicks were being silently ignored by sliders that had already rendered once.
6. **CSV download exported all 24 internal columns** instead of just the columns visible in the on-screen table, contradicting the spec's literal wording ("all visible columns").
7. **BSE's servers return 403 Forbidden to requests without a browser-like `User-Agent` header**, causing every genuinely working annual report link to be falsely flagged as "unavailable" by the live-check feature. Confirmed by directly testing the same URL with and without the header (403 vs. 200).
8. **Company Profile's pros/cons section only showed the first `prosandcons` row per company**, silently dropping additional rows — found during Day 27's systematic 10-ticker QA pass (INFY has 2 rows, only 1 was being shown).

## Data quality findings

- **ATGL has zero rows in the `cashflow` table** — a genuine pre-existing gap, not introduced this sprint. The Capital Allocation Map correctly shows 91/92 companies with a visible caption explaining why, rather than silently under-counting.
- Confirmed no company has zero rows in `financial_ratios` or `profitandloss` (the two most structurally critical tables) — the worst real cases are ATGL (no cashflow) and JIOFIN/ADANIGREEN (short listing history), both handled gracefully throughout every screen.

## Day 27 QA summary

Tested 10 tickers spanning all 5 required sectors (IT, Financials, Consumer Staples, Energy, Healthcare) against every core data function — no crashes. Extreme screener slider values tested at both ends (all-permissive → 66/92 companies; all-restrictive → 0, clean empty table, CSV still works). Chart sizing verified responsive at narrower browser widths. Company Profile load time measured at 7-26ms for backend queries across 5 tickers, comfortably under the 3-second requirement, confirmed in the live browser as well.

## What's NOT done / left for later

- Real click-driven treemap interactivity (dropdown substitute used instead — functionally equivalent, less visually direct).
- The live BSE link-availability check adds real network latency per report year; acceptable for an optional, user-triggered checkbox, but not something to run automatically on every page load.

## Exit criteria — final status

| Criterion | Status |
|---|---|
| All 8 Streamlit screens load without errors for any of the 92 tickers | ✅ Verified across 10 tickers spanning 5 sectors, plus edge cases (JIOFIN, ADANIGREEN, ATGL) |
| Company Profile screen loads in under 3 seconds | ✅ 7-26ms backend, confirmed fast in live browser |
| Screener CSV download produces a valid file with correct column headers | ✅ Fixed to match exactly the visible on-screen columns |
| `valuation_summary.xlsx` has 92 rows with all required columns | ✅ |
| Sprint 4 review demo completed — team lead signs off | Requires an actual human review meeting, not completable in code |