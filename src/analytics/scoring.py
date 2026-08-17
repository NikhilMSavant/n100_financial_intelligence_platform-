"""Sprint 3 — composite quality score with P10/P90 winsorisation and
sector-relative normalisation."""
import numpy as np
import pandas as pd


def winsorize_scale_0_100(series: pd.Series, higher_is_better=True):
    """Cap at P10/P90 then scale linearly to 0-100."""
    s = series.astype(float)
    valid = s.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    p10, p90 = valid.quantile(0.10), valid.quantile(0.90)
    capped = s.clip(lower=p10, upper=p90)
    if p90 == p10:
        scaled = pd.Series(50.0, index=series.index)
    else:
        scaled = (capped - p10) / (p90 - p10) * 100
    if not higher_is_better:
        scaled = 100 - scaled
    return scaled


def de_score(de_series: pd.Series):
    # 0->100, 0.5->85, 1->70, 2->50, >5->0 -- piecewise linear interpolation on anchor points
    anchors_x = [0, 0.5, 1, 2, 5]
    anchors_y = [100, 85, 70, 50, 0]

    def score_one(v):
        if pd.isna(v):
            return np.nan
        if v >= 5:
            return 0.0
        return float(np.interp(v, anchors_x, anchors_y))
    return de_series.apply(score_one)


def icr_score(icr_series: pd.Series, icr_label_series: pd.Series):
    anchors_x = [1.5, 3, 5, 10]
    anchors_y = [0, 50, 75, 100]

    def score_one(v, lbl):
        if lbl == "Debt Free":
            return 100.0
        if pd.isna(v):
            return np.nan
        if v >= 10:
            return 100.0
        if v <= 1.5:
            return 0.0
        return float(np.interp(v, anchors_x, anchors_y))
    return [score_one(v, l) for v, l in zip(icr_series, icr_label_series)]


def compute_composite_score(ratios_latest: pd.DataFrame, sector_relative=False):
    """ratios_latest: one row per company (latest year), with sector column if sector_relative."""
    df = ratios_latest.copy()

    def scale(col, higher_is_better=True):
        if sector_relative and "broad_sector" in df.columns:
            return df.groupby("broad_sector")[col].transform(
                lambda s: winsorize_scale_0_100(s, higher_is_better))
        return winsorize_scale_0_100(df[col], higher_is_better)

    roe_s = scale("return_on_equity_pct")
    roce_s = scale("return_on_capital_employed_pct")
    npm_s = scale("net_profit_margin_pct")
    fcf_cagr_s = scale("free_cash_flow_cr")  # proxy: FCF level; true 5yr FCF CAGR not stored per-row here
    cfo_pat_s = scale("cfo_pat_ratio")
    fcf_flag_s = df["free_cash_flow_cr"].apply(lambda v: 100.0 if pd.notna(v) and v > 0 else 0.0)
    rev_cagr_s = df["revenue_cagr_5yr"].fillna(0).clip(lower=-30, upper=50)
    rev_cagr_s = (rev_cagr_s + 30) / 80 * 100
    rev_cagr_s = np.where(df["revenue_cagr_5yr_flag"].notna() & (df["revenue_cagr_5yr_flag"] != ""), 0, rev_cagr_s)
    pat_cagr_s = df["pat_cagr_5yr"].fillna(0).clip(lower=-30, upper=50)
    pat_cagr_s = (pat_cagr_s + 30) / 80 * 100
    pat_cagr_s = np.where(df["pat_cagr_5yr_flag"].notna() & (df["pat_cagr_5yr_flag"] != ""), 0, pat_cagr_s)
    de_s = de_score(df["debt_to_equity"])
    icr_s = icr_score(df["interest_coverage"], df["icr_label"])

    score = (
        0.15 * roe_s.fillna(0) + 0.10 * roce_s.fillna(0) + 0.10 * npm_s.fillna(0)
        + 0.15 * fcf_cagr_s.fillna(0) + 0.10 * cfo_pat_s.fillna(0) + 0.05 * fcf_flag_s.fillna(0)
        + 0.10 * pd.Series(rev_cagr_s, index=df.index).fillna(0)
        + 0.10 * pd.Series(pat_cagr_s, index=df.index).fillna(0)
        + 0.10 * de_s.fillna(0) + 0.05 * pd.Series(icr_s, index=df.index).fillna(0)
    )
    return score.clip(0, 100)
