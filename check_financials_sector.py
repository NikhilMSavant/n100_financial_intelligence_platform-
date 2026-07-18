import sqlite3
conn = sqlite3.connect('db/nifty100.db')
count = conn.execute("SELECT COUNT(*) FROM sectors WHERE broad_sector = 'Financials'").fetchone()[0]
print(f'Financials sector companies: {count}')
names = conn.execute("SELECT company_id FROM sectors WHERE broad_sector = 'Financials'").fetchall()
print([n[0] for n in names])