import sqlite3
conn = sqlite3.connect('db/nifty100.db')

for company in ['BEL', 'HAL', 'LT', 'PNB', 'TCS']:
    row = conn.execute("""
        SELECT bs.year, bs.equity_capital, bs.reserves, pl.net_profit
        FROM balancesheet bs
        JOIN profitandloss pl ON pl.company_id = bs.company_id AND pl.year = bs.year
        WHERE bs.company_id = ?
        ORDER BY bs.year DESC LIMIT 1
    """, (company,)).fetchone()
    print(company, row)