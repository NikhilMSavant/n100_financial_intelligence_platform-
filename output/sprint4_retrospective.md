# Sprint 4 Retrospective — Dashboard & Valuation Module

## Valuation module (Day 26)
- FCF yield = latest-year FCF / latest-year market cap, both in Crore.
- Sector median P/E computed cross-sectionally in the latest year only (per spec).
- Flags: Caution if P/E > 1.5x sector median, Discount if P/E < 0.7x sector median, else Fair.
- output/valuation_summary.xlsx: 92 rows (all companies). output/valuation_flags.csv: 44
  flagged (14 Caution, 30 Discount) on this dataset.

## Dashboard (Day 22-25)
Built as a standard Streamlit multi-page app (`src/dashboard/app.py` + `pages/01..08`),
with every DB query routed through `src/dashboard/utils/db.py` and cached via
`@st.cache_data(ttl=600)`.

**Environment constraint**: the build sandbox has no outbound network access, so
`streamlit` and `plotly` could not be `pip install`-ed here, and the dashboard could
not be executed/screenshotted in this session. All 8 page files were syntax-checked
with `python3 -m py_compile` (all pass) and reviewed line-by-line against the DB
schema and the Sprint 4 spec. **Before the Day 27 sign-off demo, run
`pip install -r requirements.txt` and `streamlit run src/dashboard/app.py` in an
environment with network access to do the live click-through QA** (10 tickers across
sectors, partial-data tickers, extreme slider values) called for in Day 27 -- this
step could not be completed inside the current sandbox and is the one open item
carried into the Sprint 4 sign-off.

## Defensive-coding pass applied without live testing
- Company Profile: unknown ticker -> "Ticker not found — please try another" (no crash).
- Company Profile / Trend / Peers: guards for `ratios.empty` before indexing `.iloc[-1]`.
- Screener: sliders operate on `.fillna()`-guarded columns so a None metric doesn't
  raise; CSV export only includes columns present in the result frame.
- Sector Analysis: revenue pulled fresh from `profitandloss` (latest year) rather than
  assumed present in `financial_ratios`, since that table doesn't store `sales` directly.
- Annual Reports: URL health-check wrapped in try/except -- network failures render as
  "unverified" rather than crashing the page or falsely flagging "unavailable".

## Still open for Day 27 sign-off (requires a networked environment)
- Live click-through of all 8 screens on 10 tickers spanning IT/Financials/FMCG/Energy/Healthcare.
- Company Profile load-time measurement (<3s target).
- Visual confirmation that Plotly charts don't overflow the page width at common
  viewport sizes.
