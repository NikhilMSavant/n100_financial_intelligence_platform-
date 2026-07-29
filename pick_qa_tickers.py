import sqlite3
conn = sqlite3.connect("db/nifty100.db")

for sector in ["Information Technology", "Financials", "Consumer Staples", "Energy", "Healthcare"]:
    rows = conn.execute("SELECT company_id FROM sectors WHERE broad_sector = ? LIMIT 2", (sector,)).fetchall()
    print(sector, "->", [r[0] for r in rows])