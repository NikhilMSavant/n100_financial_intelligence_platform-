import time
import sys
sys.path.insert(0, "src/dashboard/utils")
from db import get_companies, get_ratios, get_pl, get_pros_cons

tickers = ["TCS", "RELIANCE", "HDFCBANK", "INFY", "ASIANPAINT"]

for t in tickers:
    start = time.time()
    companies = get_companies.__wrapped__()
    ratios = get_ratios.__wrapped__(t)
    pl = get_pl.__wrapped__(t)
    pros_cons = get_pros_cons.__wrapped__(t)
    elapsed = time.time() - start
    print(f"{t:12s} {elapsed*1000:.1f} ms")