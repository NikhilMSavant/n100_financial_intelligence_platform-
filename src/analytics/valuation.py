"""
valuation.py
------------
Day 26 deliverable: FCF yield, sector-relative P/E overvaluation flags,
output/valuation_summary.xlsx and output/valuation_flags.csv.
"""
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"


def compute_fcf_yield(fcf_cr, market_cap_crore):
    """FCF Yield % = FCF / market_cap_crore * 100. None if market_cap missing/zero."""
    if market_cap_crore is None or market_cap_crore == 0 or fcf_cr is None:
        return None
    return (fcf_cr / market_cap_crore) * 100


def classify_valuation_flag(pe_ratio, sector_median_pe):
    """
    Caution if P/E > sector_median * 1.5
    Discount if P/E < sector_median * 0.7
    Fair otherwise.
    Returns None if either input is missing (can't judge without both).
    """
    if pe_ratio is None or sector_median_pe is None or sector_median_pe == 0:
        return None
    if pe_ratio > sector_median_pe * 1.5:
        return "Caution"
    if pe_ratio < sector_median_pe * 0.7:
        return "Discount"
    return "Fair"


def compute_valuation_summary(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)

    # latest year's P/E, P/B, EV/EBITDA, market_cap, and FCF per company
    latest = pd.read_sql("""
        SELECT mc.company_id, mc.year, mc.pe_ratio, mc.pb_ratio, mc.ev_ebitda,
               mc.market_cap_crore, fr.free_cash_flow_cr, s.broad_sector,
               c.company_name
        FROM market_cap mc
        LEFT JOIN financial_ratios fr ON fr.company_id = mc.company_id AND fr.year = mc.year
        LEFT JOIN sectors s ON s.company_id = mc.company_id
        LEFT JOIN companies c ON c.company_id = mc.company_id
        WHERE mc.year = (
            SELECT MAX(year) FROM market_cap mc2
            WHERE mc2.company_id = mc.company_id
        )
    """, conn)

    # 5-year median P/E per company (all available years, up to 5 most recent)
    all_pe = pd.read_sql("SELECT company_id, year, pe_ratio FROM market_cap ORDER BY company_id, year", conn)
    median_pe_5yr = (
        all_pe.groupby("company_id")
        .apply(lambda g: g.tail(5)["pe_ratio"].median(), include_groups=False)
        .reset_index(name="median_pe_5yr")
    )

    conn.close()

    df = latest.merge(median_pe_5yr, on="company_id", how="left")

    # sector median P/E, computed from the same latest-year snapshot
    sector_median_pe = df.groupby("broad_sector")["pe_ratio"].median().rename("sector_median_pe")
    df = df.merge(sector_median_pe, on="broad_sector", how="left")

    df["fcf_yield_pct"] = df.apply(lambda r: compute_fcf_yield(r["free_cash_flow_cr"], r["market_cap_crore"]), axis=1)
    df["pe_vs_sector_median_pct"] = df.apply(
        lambda r: ((r["pe_ratio"] - r["sector_median_pe"]) / r["sector_median_pe"] * 100)
        if pd.notna(r["pe_ratio"]) and pd.notna(r["sector_median_pe"]) and r["sector_median_pe"] != 0
        else None,
        axis=1,
    )
    df["flag"] = df.apply(lambda r: classify_valuation_flag(r["pe_ratio"], r["sector_median_pe"]), axis=1)

    return df[[
        "company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio",
        "ev_ebitda", "fcf_yield_pct", "median_pe_5yr", "pe_vs_sector_median_pct", "flag",
    ]].rename(columns={"broad_sector": "sector", "median_pe_5yr": "5yr_median_PE",
                        "pe_vs_sector_median_pct": "PE_vs_sector_median_pct"})


def write_valuation_table(df, db_path=DB_PATH):
    """Writes the valuation summary into a 'valuation' table in SQLite,
    so the dashboard's get_valuation(ticker) function (stubbed on Day 22)
    can query it directly."""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS valuation")
    df.to_sql("valuation", conn, index=False)
    conn.close()


def main():
    df = compute_valuation_summary()

    df.to_excel("output/valuation_summary.xlsx", index=False)
    print(f"Wrote output/valuation_summary.xlsx: {len(df)} rows")

    flagged = df[df["flag"].isin(["Caution", "Discount"])]
    flagged.to_csv("output/valuation_flags.csv", index=False)
    print(f"Wrote output/valuation_flags.csv: {len(flagged)} rows")

    write_valuation_table(df)
    print("Wrote 'valuation' table to database")

    print("\nFlag distribution:")
    print(df["flag"].value_counts(dropna=False))


if __name__ == "__main__":
    main()