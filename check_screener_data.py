import sqlite3
conn = sqlite3.connect('db/nifty100.db')

print("financial_ratios columns:")
for c in conn.execute("PRAGMA table_info(financial_ratios)").fetchall():
    print(" ", c[1])

print("\nmarket_cap columns:")
for c in conn.execute("PRAGMA table_info(market_cap)").fetchall():
    print(" ", c[1])

print("\nprofitandloss columns (checking for net_profit, sales):")
for c in conn.execute("PRAGMA table_info(profitandloss)").fetchall():
    print(" ", c[1])