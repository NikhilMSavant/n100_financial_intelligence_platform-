import sqlite3
conn = sqlite3.connect("db/nifty100.db")

rows = conn.execute("SELECT * FROM cashflow WHERE company_id = 'ATGL'").fetchall()
print("ATGL cashflow rows:", len(rows))
for r in rows:
    print(r)