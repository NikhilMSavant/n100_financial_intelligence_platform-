import sqlite3
conn = sqlite3.connect("db/nifty100.db")

cols = [c[1] for c in conn.execute("PRAGMA table_info(companies)").fetchall()]
print("companies columns:", cols)

sample = conn.execute("SELECT * FROM peer_percentiles WHERE peer_group_name = 'IT Services' LIMIT 5").fetchall()
for row in sample:
    print(row)