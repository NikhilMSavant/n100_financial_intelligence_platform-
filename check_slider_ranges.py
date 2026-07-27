import sys
sys.path.insert(0, "src/screener")
from engine import load_screener_universe

df = load_screener_universe()

metrics = ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
           "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct",
           "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage"]

for m in metrics:
    col = df[m].dropna()
    print(f"{m:30s} min={col.min():.2f}  max={col.max():.2f}  median={col.median():.2f}")