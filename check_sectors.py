import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT broad_sector, COUNT(*) as n
    FROM sectors
    GROUP BY broad_sector
    ORDER BY n DESC
""").fetchall()
for sector, n in rows:
    print(f"{sector}: {n} companies")