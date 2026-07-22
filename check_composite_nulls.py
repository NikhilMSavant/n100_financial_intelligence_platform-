from src.screener.engine import load_screener_universe
from src.screener.composite_score import (
    sanitize_known_bad_values, winsorize_scale, KNOWN_BAD_ROE_ROCE_COMPANIES
)
import pandas as pd

df = load_screener_universe()
df = sanitize_known_bad_values(df)
known_bad_mask = df["company_id"].isin(KNOWN_BAD_ROE_ROCE_COMPANIES)

roe_score = winsorize_scale(df["return_on_equity_pct"], exclude_from_boundaries=known_bad_mask)
roce_score = winsorize_scale(df["return_on_capital_employed_pct"], exclude_from_boundaries=known_bad_mask)
npm_score = winsorize_scale(df["net_profit_margin_pct"])
fcf_cagr_score = winsorize_scale(df["fcf_cagr_5yr"])
revenue_cagr_score = winsorize_scale(df["revenue_cagr_5yr"])
pat_cagr_score = winsorize_scale(df["pat_cagr_5yr"])
de_score_raw = winsorize_scale(df["debt_to_equity"])

for name, s in [("roe", roe_score), ("roce", roce_score), ("npm", npm_score),
                ("fcf_cagr", fcf_cagr_score), ("revenue_cagr", revenue_cagr_score),
                ("pat_cagr", pat_cagr_score), ("de", de_score_raw)]:
    print(f"{name}: {s.notna().sum()}/{len(s)} non-null")


cfo_pat_ratio = df.apply(
    lambda r: (r["cash_from_operations_cr"] / r["net_profit"])
    if pd.notna(r["cash_from_operations_cr"]) and pd.notna(r["net_profit"]) and r["net_profit"] != 0
    else None,
    axis=1,
)
fcf_positive_raw = df["free_cash_flow_cr"].apply(lambda v: 100.0 if pd.notna(v) and v > 0 else (0.0 if pd.notna(v) else None))
cfo_pat_score = winsorize_scale(cfo_pat_ratio)

icr_col = df["interest_coverage"].copy()
is_debt_free = icr_col.isna()
icr_winsorized = winsorize_scale(icr_col)
icr_final = icr_winsorized.where(~is_debt_free, 100.0)

print(f"cfo_pat_score: {cfo_pat_score.notna().sum()}/92 non-null")
print(f"fcf_positive_raw: {fcf_positive_raw.notna().sum()}/92 non-null")
print(f"icr_final: {icr_final.notna().sum()}/92 non-null")