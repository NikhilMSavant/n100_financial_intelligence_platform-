import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT company_id, metric, value
    FROM peer_percentiles
    WHERE peer_group_name = 'Automobiles' AND metric = 'pat_cagr_5yr'
""").fetchall()
for r in rows:
    print(r)