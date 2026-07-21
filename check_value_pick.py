from src.screener.engine import load_screener_universe, run_preset

df = load_screener_universe()
for preset in ["Quality Compounder", "Value Pick", "Growth Accelerator", "Dividend Champion", "Debt-Free Blue Chip", "Turnaround Watch"]:
    result = run_preset(df, preset)
    print(f"{preset}: {len(result)} companies")