import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("SELECT company_id, company_name FROM companies ORDER BY company_id").fetchall()
for cid, name in rows:
    print(cid, "->", name)