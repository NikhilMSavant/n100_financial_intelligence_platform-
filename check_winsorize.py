from src.screener.engine import load_screener_universe
from src.screener.composite_score import winsorize_scale, sanitize_known_bad_values, KNOWN_BAD_ROE_ROCE_COMPANIES

df = load_screener_universe()
df = sanitize_known_bad_values(df)

known_bad_mask = df["company_id"].isin(KNOWN_BAD_ROE_ROCE_COMPANIES)
scaled = winsorize_scale(df["return_on_equity_pct"], exclude_from_boundaries=known_bad_mask)

result = df[["company_id", "return_on_equity_pct"]].copy()
result["scaled"] = scaled
print(result.sort_values("return_on_equity_pct", ascending=False).head(15).to_string())