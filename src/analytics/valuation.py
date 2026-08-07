"""
valuation.py — Sprint 4 / Day 26
Computes FCF yield, sector-median P/E comparison, and Caution/Discount/Fair
flags for all companies using market_cap.xlsx data (loaded into market_cap table).
"""
import os
import sqlite3
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "output")


def run():
    conn = sqlite3.connect(DB_PATH)
    mc = pd.read_sql("SELECT * FROM market_cap", conn)
    idx = mc.groupby("company_id")["year"].idxmax()
    latest_mc = mc.loc[idx].reset_index(drop=True)
    latest_year = latest_mc["year"].max()

    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr_idx = fr.groupby("company_id")["year"].idxmax()
    latest_fr = fr.loc[fr_idx].reset_index(drop=True)

    df = latest_mc.merge(companies, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(latest_fr[["company_id", "free_cash_flow_cr"]], on="company_id", how="left")

    # FCF yield
    df["fcf_yield_pct"] = df["free_cash_flow_cr"] / df["market_cap_crore"] * 100

    # 5yr median PE per company (from full market_cap history)
    med_pe = mc.groupby("company_id")["pe_ratio"].median().rename("5yr_median_PE")
    df = df.merge(med_pe, on="company_id", how="left")

    # sector median PE, latest year only
    sector_pe = df.groupby("broad_sector")["pe_ratio"].median().rename("sector_median_pe")
    df = df.merge(sector_pe, on="broad_sector", how="left")

    df["PE_vs_sector_median_pct"] = (df["pe_ratio"] - df["sector_median_pe"]) / df["sector_median_pe"] * 100

    def flag(row):
        if pd.isna(row["pe_ratio"]) or pd.isna(row["sector_median_pe"]) or row["sector_median_pe"] == 0:
            return "Fair"
        if row["pe_ratio"] > row["sector_median_pe"] * 1.5:
            return "Caution"
        if row["pe_ratio"] < row["sector_median_pe"] * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = df.apply(flag, axis=1)

    out = df.rename(columns={
        "broad_sector": "sector", "pe_ratio": "P/E", "pb_ratio": "P/B",
        "ev_ebitda": "EV/EBITDA",
    })[["company_id", "company_name", "sector", "P/E", "P/B", "EV/EBITDA",
        "fcf_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct", "flag"]]
    out = out.rename(columns={"fcf_yield_pct": "FCF_yield_pct"})

    out.to_excel(os.path.join(OUT_DIR, "valuation_summary.xlsx"), index=False)
    flagged = out[out["flag"].isin(["Caution", "Discount"])]
    flagged.to_csv(os.path.join(OUT_DIR, "valuation_flags.csv"), index=False)

    print(f"valuation_summary.xlsx: {len(out)} companies")
    print(f"valuation_flags.csv: {len(flagged)} flagged "
          f"(Caution={sum(out.flag=='Caution')}, Discount={sum(out.flag=='Discount')})")
    conn.close()
    return out


if __name__ == "__main__":
    run()
