from src.screener.engine import load_screener_universe

df = load_screener_universe()
extra_cols = ["pat_cagr_5yr", "operating_profit_margin_pct", "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage"]
for c in extra_cols:
    print(c, "- missing:", df[c].isna().sum(), "/", len(df))