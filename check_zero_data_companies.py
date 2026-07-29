import sqlite3
conn = sqlite3.connect("db/nifty100.db")

all_companies = set(r[0] for r in conn.execute("SELECT company_id FROM companies").fetchall())
has_ratios = set(r[0] for r in conn.execute("SELECT DISTINCT company_id FROM financial_ratios").fetchall())
has_pl = set(r[0] for r in conn.execute("SELECT DISTINCT company_id FROM profitandloss").fetchall())

print("Companies with ZERO financial_ratios rows:", all_companies - has_ratios)
print("Companies with ZERO profitandloss rows:", all_companies - has_pl)