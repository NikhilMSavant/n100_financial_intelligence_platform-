from src.screener.engine import load_screener_universe, run_preset
from src.screener.composite_score import compute_scores_for_universe

df = load_screener_universe()
scored = compute_scores_for_universe(df)
result = run_preset(scored, "Quality Compounder")
result = result.sort_values("final_composite_score", ascending=False)

print("=== Quality Compounder top 5 ===")
print(result[["company_id", "return_on_equity_pct", "debt_to_equity",
              "free_cash_flow_cr", "revenue_cagr_5yr", "final_composite_score"]].head(5).to_string())

print("\n=== IT Services peer ranking check ===")
import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT company_id, value, percentile_rank
    FROM peer_percentiles
    WHERE peer_group_name = 'IT Services' AND metric = 'roe'
    ORDER BY value DESC
""").fetchall()
for r in rows:
    print(r)