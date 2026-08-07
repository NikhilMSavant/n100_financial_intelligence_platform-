"""
cashflow_intelligence_report.py — Sprint 5 / Day 31-32
Builds output/cashflow_intelligence.xlsx, output/distress_alerts.csv and
output/pattern_changes.csv from financial_ratios + cashflow + capital_allocation.csv.
"""
import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from cashflow_kpis import distress_signal, deleveraging_flag

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "output")


def cfo_quality_label(score):
    if score is None or pd.isna(score):
        return None
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_label(pct):
    if pct is None or pd.isna(pct):
        return None
    if pct < 3:
        return "Asset Light"
    if pct <= 8:
        return "Moderate"
    return "Capital Intensive"


def run():
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    bs = pd.read_sql("SELECT company_id, year, borrowings FROM balancesheet ORDER BY company_id, year", conn)
    pl = pd.read_sql("SELECT company_id, year, net_profit FROM profitandloss ORDER BY company_id, year", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)

    cap_path = os.path.join(OUT_DIR, "capital_allocation.csv")
    cap = pd.read_csv(cap_path) if os.path.exists(cap_path) else pd.DataFrame()

    idx = fr.groupby("company_id")["year"].idxmax()
    latest_fr = fr.loc[idx].reset_index(drop=True)

    rows, distress_rows = [], []
    for _, row in latest_fr.iterrows():
        cid, year = row.company_id, row.year
        cfo_label = cfo_quality_label(row.cfo_quality_score)
        cx_label = capex_label(row.capex_intensity_pct)

        cf_latest = cf[(cf.company_id == cid) & (cf.year == year)]
        bs_hist = bs[bs.company_id == cid].sort_values("year")
        pl_latest = pl[(pl.company_id == cid) & (pl.year == year)]

        cfo_val = cf_latest["operating_activity"].iloc[0] if len(cf_latest) else None
        cff_val = cf_latest["financing_activity"].iloc[0] if len(cf_latest) else None
        distress = distress_signal(cfo_val, cff_val)

        this_yr_borrow = bs_hist[bs_hist.year == year]["borrowings"]
        prior_yr_borrow = bs_hist[bs_hist.year == year - 1]["borrowings"]
        deleveraging = deleveraging_flag(
            cff_val, this_yr_borrow.iloc[0] if len(this_yr_borrow) else None,
            prior_yr_borrow.iloc[0] if len(prior_yr_borrow) else None)

        cap_row = cap[(cap.company_id == cid) & (cap.year == year)] if len(cap) else pd.DataFrame()
        pattern_label = cap_row["pattern_label"].iloc[0] if len(cap_row) else None

        sector = sectors.set_index("company_id")["broad_sector"].get(cid)

        rows.append(dict(
            company_id=cid, sector=sector, cfo_quality_score=row.cfo_quality_score,
            cfo_quality_label=cfo_label, capex_intensity_pct=row.capex_intensity_pct,
            capex_label=cx_label, fcf_cagr_5yr=None,  # not separately tracked; see note in retro
            fcf_conversion_pct=row.fcf_conversion_pct, distress_flag=distress,
            deleveraging_flag=deleveraging, capital_allocation_label=pattern_label,
        ))

        if distress:
            net_profit_val = pl_latest["net_profit"].iloc[0] if len(pl_latest) else None
            distress_rows.append(dict(company_id=cid, year=year, cfo=cfo_val, cff=cff_val,
                                       latest_net_profit=net_profit_val))

    cfi_df = pd.DataFrame(rows).merge(companies, on="company_id", how="left")
    cfi_df = cfi_df[["company_id", "company_name", "sector", "cfo_quality_score", "cfo_quality_label",
                      "capex_intensity_pct", "capex_label", "fcf_cagr_5yr", "fcf_conversion_pct",
                      "distress_flag", "deleveraging_flag", "capital_allocation_label"]]
    cfi_df.to_excel(os.path.join(OUT_DIR, "cashflow_intelligence.xlsx"), index=False)

    distress_df = pd.DataFrame(distress_rows)
    distress_df.to_csv(os.path.join(OUT_DIR, "distress_alerts.csv"), index=False)

    # Pattern distribution summary (latest year)
    if len(cap):
        cap_idx = cap.groupby("company_id")["year"].idxmax()
        latest_cap = cap.loc[cap_idx]
        dist_summary = latest_cap["pattern_label"].value_counts().reset_index()
        dist_summary.columns = ["pattern_label", "n_companies"]
        dist_summary.to_csv(os.path.join(OUT_DIR, "capital_allocation_distribution.csv"), index=False)

        # Pattern changes year-over-year
        cap_sorted = cap.sort_values(["company_id", "year"])
        cap_sorted["prev_pattern"] = cap_sorted.groupby("company_id")["pattern_label"].shift(1)
        changes = cap_sorted[cap_sorted["prev_pattern"].notna() &
                              (cap_sorted["prev_pattern"] != cap_sorted["pattern_label"])]
        changes = changes[["company_id", "year", "prev_pattern", "pattern_label"]].rename(
            columns={"pattern_label": "new_pattern"})
        changes.to_csv(os.path.join(OUT_DIR, "pattern_changes.csv"), index=False)
        print(f"pattern_changes.csv: {len(changes)} year-over-year pattern changes")

    print(f"cashflow_intelligence.xlsx: {len(cfi_df)} rows")
    print(f"distress_alerts.csv: {len(distress_df)} flagged companies")
    conn.close()
    return cfi_df, distress_df


if __name__ == "__main__":
    run()
