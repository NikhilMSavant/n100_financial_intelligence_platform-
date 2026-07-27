import sys
sys.path.insert(0, "src/dashboard/utils")
import db
import pandas as pd

conn = db._connect()
df = pd.read_sql("""
    SELECT company_id, COUNT(DISTINCT year) as n
    FROM profitandloss
    WHERE year != 'TTM'
    GROUP BY company_id
    ORDER BY n ASC
    LIMIT 5
""", conn)
print(df)
