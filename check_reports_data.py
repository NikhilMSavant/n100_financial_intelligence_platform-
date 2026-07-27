import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("SELECT year, annual_report FROM documents WHERE company_id = 'TCS' ORDER BY year").fetchall()
for r in rows:
    print(r)