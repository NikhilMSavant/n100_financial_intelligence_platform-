"""
Day 11 deliverable: generates output/capital_allocation.csv by running
classify_capital_allocation() against every company-year in cashflow,
using profitandloss net_profit as the PAT denominator for CFO quality.
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from cashflow_kpis import classify_capital_allocation

DB_PATH = "db/nifty100.db"
OUT_PATH = "output/capital_allocation.csv"


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT cf.company_id, cf.year, cf.operating_activity,
               cf.investing_activity, cf.financing_activity, pl.net_profit
        FROM cashflow cf
        LEFT JOIN profitandloss pl
          ON pl.company_id = cf.company_id AND pl.year = cf.year
        ORDER BY cf.company_id, cf.year
    """).fetchall()

    results = []
    for company_id, year, cfo, cfi, cff, net_profit in rows:
        cfo_quality_value = None
        if cfo is not None and net_profit and net_profit != 0:
            cfo_quality_value = cfo / net_profit

        if cfo is None or cfi is None or cff is None:
            classified = {"cfo_sign": "N/A", "cfi_sign": "N/A", "cff_sign": "N/A", "pattern_label": "Incomplete Data"}
        else:
            classified = classify_capital_allocation(cfo, cfi, cff, cfo_quality_value)
        results.append({
            "company_id": company_id,
            "year": year,
            "cfo_sign": classified["cfo_sign"],
            "cfi_sign": classified["cfi_sign"],
            "cff_sign": classified["cff_sign"],
            "pattern_label": classified["pattern_label"],
        })

    conn.close()

    os.makedirs("output", exist_ok=True)
    import csv
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Wrote {OUT_PATH}: {len(results)} rows")


if __name__ == "__main__":
    main()