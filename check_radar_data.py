from src.screener.engine import load_screener_universe
from src.screener.composite_score import compute_scores_for_universe

df = load_screener_universe()
scored = compute_scores_for_universe(df)
print(scored.columns.tolist())
print(scored[["company_id", "return_on_equity_pct", "return_on_capital_employed_pct",
              "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr",
              "pat_cagr_5yr", "revenue_cagr_5yr", "final_composite_score"]].head(3))