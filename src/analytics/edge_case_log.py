"""
edge_case_log.py
----------------
Day 13 deliverable: cross-checks our computed ROCE/ROE against the
pre-computed roce_percentage/roe_percentage columns in companies.xlsx,
logging anomalies (>5% difference) to output/ratio_edge_cases.log.

Uses the most recent fiscal year's computed ratio per company for the
comparison, since companies.xlsx's pre-computed values are a single
snapshot, not a time series.
"""
import sqlite3

DB_PATH = "db/nifty100.db"
LOG_PATH = "output/ratio_edge_cases.log"
DIFF_THRESHOLD_PCT = 5.0


def main():
    conn = sqlite3.connect(DB_PATH)

    # latest computed ROE/ROCE per company (most recent non-TTM year)
    computed = conn.execute("""
        SELECT fr.company_id, fr.year, fr.return_on_equity_pct, fr.return_on_capital_employed_pct
        FROM financial_ratios fr
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
        )
    """).fetchall()
    computed_roe = {row[0]: row[2] for row in computed}
    computed_roce = {row[0]: row[3] for row in computed}

    reference = conn.execute("""
        SELECT company_id, roce_percentage, roe_percentage, company_name
        FROM companies
    """).fetchall()

    lines = []
    for company_id, ref_roce, ref_roe, name in reference:
        comp_roe = computed_roe.get(company_id)

        # TCS is a confirmed, individually-verified exception: source's
        # roe_percentage (0.52) is the actual error, not our calculation -
        # real-world TCS ROE is ~50%, matching our computed value.
        FORMULA_DISCREPANCY = {"TCS"}
        EXTREME_DIFF_THRESHOLD_PCT = 50.0  # beyond this, a timing/version
        # mismatch is not a plausible explanation - this size of gap points
        # to an underlying data quality problem (e.g. an understated
        # reserves figure), not just "different snapshot in time"

        if comp_roe is not None and ref_roe is not None:
            diff = abs(comp_roe - ref_roe)
            if diff > DIFF_THRESHOLD_PCT:
                if company_id in FORMULA_DISCREPANCY:
                    category = "DATA_SOURCE_ISSUE - source roe_percentage value itself appears to be a data entry error (real-world TCS ROE is ~50%, matching our computed value)"
                elif diff > EXTREME_DIFF_THRESHOLD_PCT:
                    category = "DATA_SOURCE_ISSUE - diff too large to be a timing/version mismatch; likely an understated equity/reserves figure in balancesheet.xlsx for this company"
                else:
                    category = "VERSION_DIFFERENCE - likely different fiscal year/period snapshot between our latest-year pick and source's pre-computed value"

                lines.append(
                    f"{company_id} | ROE | computed={comp_roe:.2f}% | source={ref_roe:.2f}% | "
                    f"diff={diff:.2f}% | category={category}"
                )

        comp_roce = computed_roce.get(company_id)
        if comp_roce is not None and ref_roce is not None:
            diff_roce = abs(comp_roce - ref_roce)
            if diff_roce > DIFF_THRESHOLD_PCT:
                if diff_roce > EXTREME_DIFF_THRESHOLD_PCT:
                    roce_category = "DATA_SOURCE_ISSUE - diff too large to be a timing/version mismatch; likely an understated equity/reserves/borrowings figure in balancesheet.xlsx for this company"
                else:
                    roce_category = "VERSION_DIFFERENCE - likely different fiscal year/period snapshot, or EBIT proxy (profit_before_tax) differs from source's exact EBIT definition"
                lines.append(
                    f"{company_id} | ROCE | computed={comp_roce:.2f}% | source={ref_roce:.2f}% | "
                    f"diff={diff_roce:.2f}% | category={roce_category}"
                )

    conn.close()

    with open(LOG_PATH, "w") as f:
        f.write(f"# Ratio edge cases - Day 13\n")
        f.write(f"# Threshold: >{DIFF_THRESHOLD_PCT}% difference between computed and source values\n\n")
        f.write("\n".join(lines))
        f.write("\n")

    print(f"Wrote {LOG_PATH}: {len(lines)} anomalies found")


if __name__ == "__main__":
    main()