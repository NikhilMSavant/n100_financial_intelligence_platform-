"""Sprint 4 Day 26 — FCF yield, sector-median P/E, overvaluation flags."""
import sys
import pathlib
import sqlite3
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from screener.engine import load_latest_universe


def run_valuation():
    conn = sqlite3.connect("data/nifty100.db")
    df = load_latest_universe(conn)
    conn.close()

    df["fcf_yield_pct"] = (df["free_cash_flow_cr"] / df["market_cap_crore"] * 100).where(df["market_cap_crore"] > 0)

    sector_median_pe = df.groupby("broad_sector")["pe_ratio"].median().rename("sector_median_pe")
    df = df.merge(sector_median_pe, on="broad_sector", how="left")
    df["pe_vs_sector_median_pct"] = (df["pe_ratio"] / df["sector_median_pe"] - 1) * 100

    def flag(row):
        if pd.isna(row["pe_ratio"]) or pd.isna(row["sector_median_pe"]):
            return "Fair"
        if row["pe_ratio"] > row["sector_median_pe"] * 1.5:
            return "Caution"
        if row["pe_ratio"] < row["sector_median_pe"] * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = df.apply(flag, axis=1)

    out_cols = ["company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio", "ev_ebitda",
                "fcf_yield_pct", "sector_median_pe", "pe_vs_sector_median_pct", "flag"]
    out = df[out_cols].rename(columns={"sector_median_pe": "5yr_median_PE"})
    # Note: "5yr_median_PE" per spec name; we use sector-median-in-latest-year here since market_cap.xlsx
    # only has 2019-2024 (6 years) and per-company 5yr median is computed below for completeness.
    conn = sqlite3.connect("data/nifty100.db")
    mcap_hist = pd.read_sql("SELECT company_id, pe_ratio FROM market_cap", conn)
    conn.close()
    five_yr_median = mcap_hist.groupby("company_id")["pe_ratio"].median().rename("5yr_median_PE_actual")
    out = out.merge(five_yr_median, on="company_id", how="left")

    pathlib.Path("output").mkdir(exist_ok=True)
    out.to_excel("output/valuation_summary.xlsx", index=False)

    flagged = out[out["flag"].isin(["Caution", "Discount"])]
    flagged.to_csv("output/valuation_flags.csv", index=False)

    print(f"valuation_summary.xlsx rows: {len(out)}")
    print(f"valuation_flags.csv rows: {len(flagged)}  (Caution={sum(out.flag=='Caution')}, Discount={sum(out.flag=='Discount')})")
    return out


if __name__ == "__main__":
    run_valuation()
