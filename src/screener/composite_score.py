"""
composite_score.py — Sprint 3 / Day 17
Recomputes composite_quality_score (0-100) with P10/P90 winsorisation and a
sector-relative normalisation option, per the sprint-3 weighting spec:
  35% Profitability (ROE 15 + ROCE 10 + NPM 10)
  30% Cash Quality  (FCF CAGR 15 + CFO/PAT 10 + FCF positive flag 5)
  20% Growth        (Revenue CAGR 10 + PAT CAGR 10)
  15% Leverage      (D/E score 10 + ICR score 5)
"""
import os
import sqlite3
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")


def winsorize_scale(series, p_low=10, p_high=90, higher_is_better=True):
    s = series.astype(float)
    lo, hi = np.nanpercentile(s.dropna(), p_low), np.nanpercentile(s.dropna(), p_high)
    if hi == lo:
        return pd.Series(50.0, index=s.index)
    clipped = s.clip(lo, hi)
    scaled = (clipped - lo) / (hi - lo) * 100
    if not higher_is_better:
        scaled = 100 - scaled
    return scaled.fillna(scaled.median())


def compute(df, sector_relative=False):
    """df: one row per company (latest year), must include broad_sector."""
    df = df.copy()

    def score_group(g):
        g = g.copy()
        roe_s = winsorize_scale(g["return_on_equity_pct"])
        roce_s = winsorize_scale(g["return_on_capital_employed_pct"])
        npm_s = winsorize_scale(g["net_profit_margin_pct"])
        fcf_cagr = g["free_cash_flow_cr"]  # proxy: absolute FCF level as no FCF-history CAGR column stored
        fcf_cagr_s = winsorize_scale(fcf_cagr)
        cfo_pat_s = winsorize_scale(g["cfo_quality_score"])
        fcf_pos_s = (g["free_cash_flow_cr"] > 0).astype(float) * 100
        rev_cagr_s = winsorize_scale(g["revenue_cagr_5yr"])
        pat_cagr_s = winsorize_scale(g["pat_cagr_5yr"])
        de_s = winsorize_scale(g["debt_to_equity"], higher_is_better=False)
        icr_s = winsorize_scale(g["interest_coverage"].fillna(g["interest_coverage"].max()))

        g["composite_quality_score"] = (
            0.15 * roe_s + 0.10 * roce_s + 0.10 * npm_s +
            0.15 * fcf_cagr_s + 0.10 * cfo_pat_s + 0.05 * fcf_pos_s +
            0.10 * rev_cagr_s + 0.10 * pat_cagr_s +
            0.10 * de_s + 0.05 * icr_s
        ).round(2)
        return g

    if sector_relative:
        return df.groupby("broad_sector", group_keys=False).apply(score_group)
    return score_group(df)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from engine import build_universe

    conn = sqlite3.connect(DB_PATH)
    universe = build_universe(conn)
    scored = compute(universe, sector_relative=False)
    sector_scored = compute(universe, sector_relative=True)
    print(scored[["company_id", "composite_quality_score"]].sort_values(
        "composite_quality_score", ascending=False).head(10).to_string(index=False))
