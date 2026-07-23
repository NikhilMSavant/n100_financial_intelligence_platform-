import sqlite3
conn = sqlite3.connect("db/nifty100.db")

# pick a company known to be outside any peer group and confirm graceful handling
no_group = conn.execute("""
    SELECT company_id FROM companies
    WHERE company_id NOT IN (SELECT company_id FROM peer_groups)
    LIMIT 3
""").fetchall()
print("Sample companies with no peer group:", [r[0] for r in no_group])

for cid in [r[0] for r in no_group]:
    row = conn.execute("SELECT * FROM peer_percentiles WHERE company_id = ?", (cid,)).fetchall()
    print(cid, "->", row)