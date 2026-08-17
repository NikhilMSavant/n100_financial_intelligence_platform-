"""Sprint 5 Day 29 — regex parser for analysis.xlsx text fields, plus
cross-validation against Ratio Engine computed CAGR."""
import re
import sys
import pathlib
import sqlite3
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%")

FIELD_METRIC_MAP = {
    "compounded_sales_growth": "revenue_cagr",
    "compounded_profit_growth": "pat_cagr",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}

RATIO_COL_MAP = {
    "revenue_cagr": {3: "revenue_cagr_3yr", 5: "revenue_cagr_5yr", 10: "revenue_cagr_10yr"},
    "pat_cagr": {3: "pat_cagr_3yr", 5: "pat_cagr_5yr", 10: "pat_cagr_10yr"},
}


def parse_all():
    conn = sqlite3.connect("data/nifty100.db")
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    conn.close()

    parsed_rows, failures = [], []
    for _, row in analysis.iterrows():
        cid = row["company_id"]
        for field, metric_type in FIELD_METRIC_MAP.items():
            raw = row.get(field)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            m = PATTERN.search(str(raw))
            if m:
                period, value = int(m.group(1)), float(m.group(2))
                parsed_rows.append(dict(company_id=cid, metric_type=metric_type,
                                         period_years=period, value_pct=value))
            else:
                failures.append(dict(company_id=cid, field=field, raw_value=raw))

    parsed_df = pd.DataFrame(parsed_rows)
    failures_df = pd.DataFrame(failures)

    # cross-validate parsed CAGR vs Ratio Engine computed CAGR (latest year per company)
    latest_ratios = ratios.sort_values(["company_id", "year"]).groupby("company_id").tail(1)
    divergences = []
    for _, r in parsed_df.iterrows():
        col_map = RATIO_COL_MAP.get(r["metric_type"])
        if not col_map or r["period_years"] not in col_map:
            continue
        col = col_map[r["period_years"]]
        eng_row = latest_ratios[latest_ratios.company_id == r["company_id"]]
        if eng_row.empty or col not in eng_row.columns:
            continue
        eng_val = eng_row.iloc[0][col]
        if pd.isna(eng_val):
            continue
        diff = abs(eng_val - r["value_pct"])
        if diff > 5:
            divergences.append(dict(company_id=r["company_id"], metric_type=r["metric_type"],
                                     period_years=r["period_years"], parsed_value=r["value_pct"],
                                     engine_value=round(eng_val, 2), diff=round(diff, 2)))

    pathlib.Path("output").mkdir(exist_ok=True)
    parsed_df.to_csv("output/analysis_parsed.csv", index=False)
    failures_df.to_csv("output/parse_failures.csv", index=False)
    pd.DataFrame(divergences).to_csv("output/cross_validation.csv", index=False)

    print(f"analysis_parsed.csv rows: {len(parsed_df)}")
    print(f"parse_failures.csv rows: {len(failures_df)}")
    print(f"cross_validation divergences (>5%): {len(divergences)}")
    return parsed_df, failures_df


if __name__ == "__main__":
    parse_all()
