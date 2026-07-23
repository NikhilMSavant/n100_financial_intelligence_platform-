"""
composite_score.py
-------------------
Day 17 deliverable: the detailed weighted composite quality score
(0-100), distinct from Sprint 2's simpler composite_quality_score().

Weighting per spec:
  35% Profitability: ROE (15%) + ROCE (10%) + NPM (10%)
  30% Cash Quality:  FCF CAGR (15%) + CFO/PAT ratio (10%) + FCF positive flag (5%)
  20% Growth:        Revenue CAGR (10%) + PAT CAGR (10%)
  15% Leverage:      D/E score (10%) + ICR score (5%)

Each sub-metric is normalized to 0-100 via P10/P90 winsorization (see
winsorize_scale()) BEFORE combining with these weights - winsorization
needs the full company universe to compute percentiles, so it happens
one level up in compute_scores_for_universe(), not inside this per-row
function. This module's compute_weighted_score() assumes it receives
already-normalized (0-100) sub-scores and just applies the weights.

Any missing (None) sub-score is excluded from its category's weighting,
and that category's weight is redistributed proportionally across
whichever sub-scores in that category ARE available - not silently
treated as a 0, and not left broken if e.g. FCF CAGR is null for a
Capital-heavy company that otherwise has strong fundamentals.
"""
import pandas as pd

# Companies with confirmed DATA_SOURCE_ISSUE anomalies from Sprint 2 Day 13's
# edge case log (output/ratio_edge_cases.log) - understated equity/reserves
# in balancesheet.xlsx producing impossible ROE/ROCE values. Their raw ROE
# and ROCE are treated as missing (None) for composite scoring purposes,
# rather than letting known-broken numbers tie with genuine top performers
# at the 100 ceiling. Other sub-metrics (NPM, growth, leverage, cash
# quality) for these companies are unaffected and still scored normally.
KNOWN_BAD_ROE_ROCE_COMPANIES = {"BEL", "HAL", "INDIGO", "LT", "PNB"}


def sanitize_known_bad_values(df, company_id_col="company_id"):
    """
    Returns a copy of df with return_on_equity_pct and
    return_on_capital_employed_pct set to None for companies in
    KNOWN_BAD_ROE_ROCE_COMPANIES, so their composite score reflects only
    their trustworthy sub-metrics rather than a known-broken ROE/ROCE.
    """
    result = df.copy()
    is_known_bad = result[company_id_col].isin(KNOWN_BAD_ROE_ROCE_COMPANIES)
    result.loc[is_known_bad, "return_on_equity_pct"] = None
    result.loc[is_known_bad, "return_on_capital_employed_pct"] = None
    return result



def _weighted_average(items):
    """items: list of (value, weight) tuples. Skips any item whose value
    is None OR NaN (pandas silently converts None to NaN when building a
    float Series via .apply(), so both must be checked - `NaN is not None`
    is True in Python, so a None-only check lets NaN slip through and
    poison the whole weighted sum to NaN), redistributing weight
    proportionally across the remaining ones. Returns None if every item
    is missing."""
    valid = [(v, w) for v, w in items if v is not None and not (isinstance(v, float) and v != v)]
    if not valid:
        return None
    total_weight = sum(w for _, w in valid)
    return sum(v * w for v, w in valid) / total_weight


def winsorize_scale(series, exclude_from_boundaries=None):
    """
    Takes a pandas Series of raw metric values (indexed the same as
    exclude_from_boundaries, typically by company_id) and returns a new
    Series scaled to 0-100 using P10/P90 as floor/ceiling.

    exclude_from_boundaries: an optional boolean Series (same index) - True
    for rows that should NOT influence where P10/P90 are set (e.g. known
    DATA_SOURCE_ISSUE companies from Sprint 2's edge case log, whose
    extreme values are a data quality artifact, not genuine outperformance).
    These rows are still scored using the resulting boundaries - they are
    excluded only from DEFINING the boundaries, not from the output. This
    keeps every company visible in the result while preventing a handful
    of known-bad values from compressing everyone else's score.
    """
    if exclude_from_boundaries is not None:
        boundary_source = series[~exclude_from_boundaries]
    else:
        boundary_source = series

    p10 = boundary_source.quantile(0.10)
    p90 = boundary_source.quantile(0.90)

    if p90 == p10:
        return series.apply(lambda v: 50.0 if pd.notna(v) else None)

    def scale_one(v):
        if pd.isna(v):
            return None
        if v <= p10:
            return 0.0
        if v >= p90:
            return 100.0
        return (v - p10) / (p90 - p10) * 100

    return series.apply(scale_one)


MIN_SECTOR_SIZE_FOR_RELATIVE_SCORING = 5


def winsorize_scale_by_sector(series, sector_series, exclude_from_boundaries=None):
    """
    Sector-relative version of winsorize_scale(): computes P10/P90
    separately within each broad_sector, so a company's score reflects
    performance vs its own sector peers, not the whole 92-company universe.

    Sectors with fewer than MIN_SECTOR_SIZE_FOR_RELATIVE_SCORING companies
    fall back to universe-wide winsorization instead - with only 1-4
    companies, a within-sector P10/P90 isn't statistically meaningful (it
    would just be interpolating between a couple of raw values, not a
    real percentile), so those companies are compared against the full
    universe instead, which is a more honest comparison than a fake
    sector-relative number.

    series, sector_series: same index (typically company_id positions).
    """
    result = pd.Series(index=series.index, dtype=float)

    sector_counts = sector_series.value_counts()
    small_sectors = set(sector_counts[sector_counts < MIN_SECTOR_SIZE_FOR_RELATIVE_SCORING].index)

    # universe-wide fallback boundaries, computed once, used for small sectors
    universe_exclude = exclude_from_boundaries if exclude_from_boundaries is not None else pd.Series(False, index=series.index)
    universe_scaled = winsorize_scale(series, exclude_from_boundaries=universe_exclude)

    for sector in sector_series.dropna().unique():
        sector_mask = sector_series == sector

        if sector in small_sectors:
            result[sector_mask] = universe_scaled[sector_mask]
            continue

        sector_exclude = exclude_from_boundaries[sector_mask] if exclude_from_boundaries is not None else None
        sector_scaled = winsorize_scale(series[sector_mask], exclude_from_boundaries=sector_exclude)
        result[sector_mask] = sector_scaled

    # companies with no sector at all also fall back to universe-wide
    no_sector_mask = sector_series.isna()
    if no_sector_mask.any():
        result[no_sector_mask] = universe_scaled[no_sector_mask]

    return result


def compute_weighted_score(
    roe_score, roce_score, npm_score,
    fcf_cagr_score, cfo_pat_score, fcf_positive_score,
    revenue_cagr_score, pat_cagr_score,
    de_score, icr_score,
):
    """
    All *_score arguments must already be normalized to 0-100 (or None).
    Returns the final composite score (0-100) or None if every single
    sub-score across all 4 categories is missing.
    """
    profitability = _weighted_average([(roe_score, 15), (roce_score, 10), (npm_score, 10)])
    cash_quality = _weighted_average([(fcf_cagr_score, 15), (cfo_pat_score, 10), (fcf_positive_score, 5)])
    growth = _weighted_average([(revenue_cagr_score, 10), (pat_cagr_score, 10)])
    leverage = _weighted_average([(de_score, 10), (icr_score, 5)])

    categories = [(profitability, 35), (cash_quality, 30), (growth, 20), (leverage, 15)]
    return _weighted_average(categories)


def compute_scores_for_universe(df):
    """
    Takes the full screener universe DataFrame (from load_screener_universe())
    and returns it with a new 'final_composite_score' column added.

    Handles two special normalizations:
      - D/E: lower is better, so after winsorizing normally (low D/E -> low
        score), the result is inverted (100 - score) so low D/E -> high score.
      - ICR: Debt Free companies (null interest_coverage) have no
        meaningful interest risk at all, so they're assigned the best
        possible ICR score (100) directly, rather than winsorized as
        missing data alongside genuine nulls elsewhere.
    """
    df = sanitize_known_bad_values(df)
    known_bad_mask = df["company_id"].isin(KNOWN_BAD_ROE_ROCE_COMPANIES)

    # derived sub-metrics not already columns
    cfo_pat_ratio = df.apply(
        lambda r: (r["cash_from_operations_cr"] / r["net_profit"])
        if pd.notna(r["cash_from_operations_cr"]) and pd.notna(r["net_profit"]) and r["net_profit"] != 0
        else None,
        axis=1,
    )
    fcf_positive_raw = df["free_cash_flow_cr"].apply(lambda v: 100.0 if pd.notna(v) and v > 0 else (0.0 if pd.notna(v) else None))

    # Per spec: "compute sector-relative composite score - normalise
    # within each broad_sector so scores reflect performance vs sector
    # peers". Uses winsorize_scale_by_sector() for all 9 sub-metrics,
    # which falls back to universe-wide winsorization for sectors too
    # small to support a meaningful within-sector percentile (see
    # MIN_SECTOR_SIZE_FOR_RELATIVE_SCORING).
    sectors = df["broad_sector"]

    roe_score = winsorize_scale_by_sector(df["return_on_equity_pct"], sectors, exclude_from_boundaries=known_bad_mask)
    roce_score = winsorize_scale_by_sector(df["return_on_capital_employed_pct"], sectors, exclude_from_boundaries=known_bad_mask)
    npm_score = winsorize_scale_by_sector(df["net_profit_margin_pct"], sectors)
    fcf_cagr_score = winsorize_scale_by_sector(df["fcf_cagr_5yr"], sectors)
    cfo_pat_score = winsorize_scale_by_sector(cfo_pat_ratio, sectors)
    revenue_cagr_score = winsorize_scale_by_sector(df["revenue_cagr_5yr"], sectors)
    pat_cagr_score = winsorize_scale_by_sector(df["pat_cagr_5yr"], sectors)

    # D/E: winsorize (sector-relative) then invert so LOW D/E = HIGH score
    de_score_raw = winsorize_scale_by_sector(df["debt_to_equity"], sectors)
    de_score = de_score_raw.apply(lambda v: (100 - v) if pd.notna(v) else None)

    # ICR: Debt Free companies get the best possible score (100) directly;
    # everyone else is winsorized sector-relative
    icr_score = df["interest_coverage"].copy()
    is_debt_free = icr_score.isna()
    icr_winsorized = winsorize_scale_by_sector(icr_score, sectors)
    icr_final = icr_winsorized.where(~is_debt_free, 100.0)

    scores = []
    for i in range(len(df)):
        score = compute_weighted_score(
            roe_score.iloc[i], roce_score.iloc[i], npm_score.iloc[i],
            fcf_cagr_score.iloc[i], cfo_pat_score.iloc[i], fcf_positive_raw.iloc[i],
            revenue_cagr_score.iloc[i], pat_cagr_score.iloc[i],
            de_score.iloc[i], icr_final.iloc[i],
        )
        scores.append(score)

    result = df.copy()
    result["final_composite_score"] = scores
    return result