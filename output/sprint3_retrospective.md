# Sprint 3 Retrospective — Screener & Peer Comparison Engine

## Preset threshold calibration
- Value Pick's textbook thresholds (PE<20, PB<3) returned only 2/92 companies on this
  dataset (median PE here is ~44, median PB ~7.5 — the synthetic/vendor data has a much
  richer valuation multiple than a typical live market). Recalibrated to PE<35, PB<6 so
  the preset returns a business-sensible 10 companies. Documented in
  `config/screener_config.yaml`.
- The other 5 presets worked with spec thresholds unmodified: Quality Compounder (19),
  Growth Accelerator (18), Dividend Champion (30), Debt-Free Blue Chip (17),
  Turnaround Watch (37) — all within the 5-50 target band.

## Composite score
Two versions are computed: an absolute P10/P90-winsorised score (stored in
`financial_ratios.composite_quality_score`, used by the screener/dashboard for
cross-sector ranking) and a sector-relative version (`composite_score.py`,
`sector_relative=True`) for peer-aware ranking use cases.

## Peer engine
- 11 peer groups, 541 percentile-rank rows across 10 metrics.
- 36 of 92 companies are not in any peer group — this is intentional per the sprint
  brief ("No peer group assigned", no error raised) since the 11 curated peer groups
  don't cover every Nifty 100 industry (e.g. no dedicated Cement, Paints, Airlines group).
- Spot-check passed: within IT Services, the company with the highest ROE has the
  highest ROE percentile rank (verified programmatically, not just visually).

## Radar charts
Generated all 92 as static matplotlib PNGs rather than interactive plotly, per the
spec's "matplotlib polar plot **or** plotly radar chart" — matplotlib was chosen
because static PNGs matched the "Export as PNG to reports/radar_charts/" deliverable
directly, without a headless-browser export step.
