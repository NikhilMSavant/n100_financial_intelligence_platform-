"""
parser.py — Sprint 5 / Day 29
Parses the free-text growth fields in the `analysis` table with regex,
producing output/analysis_parsed.csv (long format: company_id, metric_type,
period_years, value_pct) and logging anything that doesn't match to
output/parse_failures.csv. Cross-validates parsed 5yr/10yr CAGR values
against the ratio engine's computed CAGR and flags divergence > 5pp.
"""
import os
import re
import sqlite3
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "output")

# Primary pattern per spec: "10 Years: 21%" / "5 Years:    24%"
YEARS_RE = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%")
# Secondary known variants seen in this dataset: "TTM: 43%", "1 Year: -2%", "Last Year: 12%"
TTM_RE = re.compile(r"TTM:?\s*(-?[\d.]+)%")
LAST_YEAR_RE = re.compile(r"(?:1\s*Year|Last\s*Year):?\s*(-?[\d.]+)%")

FIELD_MAP = {
    "compounded_sales_growth_raw": "compounded_sales_growth",
    "compounded_profit_growth_raw": "compounded_profit_growth",
    "stock_price_cagr_raw": "stock_price_cagr",
    "roe_raw": "roe",
}

CAGR_COLUMN_MAP = {
    ("compounded_sales_growth", 5): "revenue_cagr_5yr",
    ("compounded_sales_growth", 10): "revenue_cagr_10yr",
    ("compounded_profit_growth", 5): "pat_cagr_5yr",
    ("compounded_profit_growth", 10): "pat_cagr_10yr",
}


def parse_cell(raw):
    """Returns (period_years, value_pct) or (None, None) if unparseable.
    period_years is an int for 'N Years', 0 for TTM, 1 for '1 Year'/'Last Year'."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, None
    s = str(raw).strip()
    m = YEARS_RE.search(s)
    if m:
        return int(m.group(1)), float(m.group(2))
    m = TTM_RE.search(s)
    if m:
        return 0, float(m.group(1))
    m = LAST_YEAR_RE.search(s)
    if m:
        return 1, float(m.group(1))
    return None, None


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    analysis = pd.read_sql("SELECT * FROM analysis", conn)

    parsed_rows, failure_rows = [], []
    for _, row in analysis.iterrows():
        for raw_col, metric_type in FIELD_MAP.items():
            raw_val = row[raw_col]
            period, value = parse_cell(raw_val)
            if period is None:
                if raw_val is not None and str(raw_val).strip():
                    failure_rows.append(dict(company_id=row.company_id, field=raw_col, raw_text=raw_val))
                continue
            parsed_rows.append(dict(company_id=row.company_id, metric_type=metric_type,
                                     period_years=period, value_pct=value))

    parsed_df = pd.DataFrame(parsed_rows)
    parsed_df.to_csv(os.path.join(OUT_DIR, "analysis_parsed.csv"), index=False)

    failures_df = pd.DataFrame(failure_rows)
    failures_df.to_csv(os.path.join(OUT_DIR, "parse_failures.csv"), index=False)

    # Cross-validate vs ratio engine CAGR
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    idx = fr.groupby("company_id")["year"].idxmax()
    latest_fr = fr.loc[idx].set_index("company_id")

    divergences = []
    for (metric_type, period), fr_col in CAGR_COLUMN_MAP.items():
        subset = parsed_df[(parsed_df.metric_type == metric_type) & (parsed_df.period_years == period)]
        for _, r in subset.iterrows():
            if r.company_id not in latest_fr.index:
                continue
            engine_val = latest_fr.loc[r.company_id, fr_col]
            if pd.isna(engine_val):
                continue
            diff = abs(engine_val - r.value_pct)
            if diff > 5:
                divergences.append(dict(company_id=r.company_id, metric_type=metric_type,
                                         period_years=period, parsed_value=r.value_pct,
                                         engine_value=round(engine_val, 2), diff_pp=round(diff, 2)))

    div_df = pd.DataFrame(divergences)
    if len(div_df):
        div_df.to_csv(os.path.join(OUT_DIR, "analysis_cagr_divergences.csv"), index=False)

    print(f"analysis_parsed.csv: {len(parsed_df)} rows")
    print(f"parse_failures.csv: {len(failures_df)} rows")
    print(f"CAGR divergences (>5pp) flagged for manual review: {len(div_df)}")
    conn.close()
    return parsed_df, failures_df


if __name__ == "__main__":
    run()
