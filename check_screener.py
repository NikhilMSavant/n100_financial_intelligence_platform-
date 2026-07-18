import sqlite3
conn = sqlite3.connect('db/nifty100.db')

# latest year per company, screened on ROE > 15% and D/E < 1
rows = conn.execute("""
    SELECT fr.company_id, fr.return_on_equity_pct, fr.debt_to_equity
    FROM financial_ratios fr
    WHERE fr.year = (
        SELECT MAX(year) FROM financial_ratios fr2
        WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
    )
    AND fr.return_on_equity_pct > 15
    AND fr.return_on_equity_pct < 200  -- excludes known DATA_SOURCE_ISSUE outliers (BEL, HAL, INDIGO -
                                        -- see output/ratio_edge_cases.log Day 13) where understated
                                        -- reserves in balancesheet.xlsx produce impossible ROE values
    AND fr.debt_to_equity < 1
    ORDER BY fr.return_on_equity_pct DESC
""").fetchall()

print(f"Companies matching ROE>15% AND D/E<1: {len(rows)}")
for r in rows:
    print(f"  {r[0]:15s} ROE={r[1]:.2f}%  D/E={r[2]:.2f}")