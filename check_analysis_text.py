import sqlite3
conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe
    FROM analysis
""").fetchall()

for r in rows[:20]:
    print(r)