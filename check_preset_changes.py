from src.screener.engine import load_screener_universe, run_preset
from src.screener.composite_score import compute_scores_for_universe

df_raw = load_screener_universe()
df_scored = compute_scores_for_universe(df_raw)

for preset in ["Quality Compounder", "Debt-Free Blue Chip"]:
    before = set(run_preset(df_raw, preset)["company_id"])
    after = set(run_preset(df_scored, preset)["company_id"])
    dropped = before - after
    print(f"{preset}: dropped {dropped}")