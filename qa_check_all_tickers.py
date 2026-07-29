import sys
sys.path.insert(0, "src/dashboard/utils")
sys.path.insert(0, "src/analytics")
sys.path.insert(0, "src/screener")

from db import get_ratios, get_pl, get_bs, get_cf, get_pros_cons, get_valuation
from radar import build_radar_dataframe

tickers = ["HCLTECH", "INFY", "AXISBANK", "BAJAJFINSV", "BRITANNIA", "DABUR",
           "ADANIENSOL", "ADANIGREEN", "APOLLOHOSP", "CIPLA"]

radar_df = build_radar_dataframe()

for t in tickers:
    errors = []
    try:
        r = get_ratios.__wrapped__(t)
        pl = get_pl.__wrapped__(t)
        bs = get_bs.__wrapped__(t)
        cf = get_cf.__wrapped__(t)
        pc = get_pros_cons.__wrapped__(t)
        val = get_valuation.__wrapped__(t)
        radar_row = radar_df[radar_df["company_id"] == t]

        print(f"{t:12s} ratios={len(r):2d}yr  pl={len(pl):2d}yr  bs={len(bs):2d}yr  cf={len(cf):2d}yr  "
              f"pros_cons={len(pc)}  valuation_rows={len(val)}  radar={'OK' if not radar_row.empty else 'MISSING'}")
    except Exception as e:
        print(f"{t:12s} ERROR: {e}")