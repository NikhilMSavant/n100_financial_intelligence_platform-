import sqlite3
import sys
sys.path.insert(0, "src/analytics")
from cagr import compute_cagr_from_series

conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT company_id, year, operating_activity, investing_activity
    FROM cashflow
    WHERE year != 'TTM'
    ORDER BY company_id, year
""").fetchall()

fcf_series = {}
for company_id, year, op, inv in rows:
    fcf = (op or 0) + (inv or 0)
    fcf_series.setdefault(company_id, {})[year] = fcf

from collections import Counter
flags = Counter()
for company_id, series in fcf_series.items():
    result = compute_cagr_from_series(series, 5)
    flags[result["flag"]] += 1

print(flags)