"""Sprint 5 Day 31-32 — CFO quality, CapEx intensity, distress/deleveraging
flags, and pattern-change tracking, aggregated per company."""
import sys
import pathlib
import sqlite3
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from analytics import cashflow_kpis as CF


def run():
    conn = sqlite3.connect("data/nifty100.db")
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    bs = pd.read_sql("SELECT company_id, year, borrowings FROM balancesheet", conn)
    pl = pd.read_sql("SELECT company_id, year, net_profit FROM profitandloss", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    capital_alloc = pd.read_csv("output/capital_allocation.csv")
    conn.close()

    rows = []
    distress_rows = []
    pattern_change_rows = []

    for cid, g in ratios.sort_values("year").groupby("company_id"):
        g = g.reset_index(drop=True)
        latest = g.iloc[-1]
        cf_g = cf[cf.company_id == cid].sort_values("year").reset_index(drop=True)
        bs_g = bs[bs.company_id == cid].sort_values("year").reset_index(drop=True)
        sector = sectors[sectors.company_id == cid]["broad_sector"]
        sector = sector.iloc[0] if not sector.empty else None

        fcf_series = g["free_cash_flow_cr"].dropna()
        fcf_cagr_5yr = None
        if len(fcf_series) >= 6:
            start, end = fcf_series.iloc[-6], fcf_series.iloc[-1]
            if start and start > 0 and end > 0:
                fcf_cagr_5yr = ((end / start) ** (1 / 5) - 1) * 100

        distress = False
        deleveraging = False
        cf_valid = cf_g.dropna(subset=["operating_activity", "investing_activity", "financing_activity"])
        if not cf_valid.empty and not bs_g.empty:
            last_cf = cf_valid.iloc[-1]
            distress = CF.distress_signal(last_cf.get("operating_activity"), last_cf.get("financing_activity"))
            bs_valid = bs_g.dropna(subset=["borrowings"])
            match_year_idx = bs_valid[bs_valid.year == last_cf["year"]].index
            if len(bs_valid) >= 2 and len(match_year_idx):
                pos = bs_valid.index.get_loc(match_year_idx[0])
                if pos >= 1:
                    deleveraging = CF.deleveraging_flag(last_cf.get("financing_activity"),
                                                         bs_valid.iloc[pos]["borrowings"], bs_valid.iloc[pos - 1]["borrowings"])

        pattern_hist = capital_alloc[(capital_alloc.company_id == cid) & (capital_alloc.pattern_label.notna())].sort_values("year")
        pattern_label_latest = pattern_hist.iloc[-1]["pattern_label"] if not pattern_hist.empty else None

        if len(pattern_hist) >= 2:
            prev_label = pattern_hist.iloc[-2]["pattern_label"]
            if prev_label != pattern_label_latest:
                pattern_change_rows.append(dict(company_id=cid, from_pattern=prev_label,
                                                  to_pattern=pattern_label_latest,
                                                  year=pattern_hist.iloc[-1]["year"]))

        rows.append(dict(
            company_id=cid, sector=sector,
            cfo_quality_score=latest.get("cfo_pat_ratio"), cfo_quality_label=latest.get("cfo_quality_label"),
            capex_intensity_pct=latest.get("capex_intensity_pct"), capex_label=latest.get("capex_label"),
            fcf_cagr_5yr=fcf_cagr_5yr, fcf_conversion_pct=latest.get("fcf_conversion_pct"),
            distress_flag=int(distress), deleveraging_flag=int(deleveraging),
            capital_allocation_label=pattern_label_latest,
        ))

        if distress:
            last_pl = pl[(pl.company_id == cid)].sort_values("year")
            latest_np = last_pl.iloc[-1]["net_profit"] if not last_pl.empty else None
            distress_rows.append(dict(company_id=cid,
                                       cfo=last_cf.get("operating_activity"),
                                       cff=last_cf.get("financing_activity"),
                                       latest_net_profit=latest_np))

    out_df = pd.DataFrame(rows)
    distress_df = pd.DataFrame(distress_rows)
    pattern_change_df = pd.DataFrame(pattern_change_rows)

    pathlib.Path("output").mkdir(exist_ok=True)
    out_df.to_excel("output/cashflow_intelligence.xlsx", index=False)
    distress_df.to_csv("output/distress_alerts.csv", index=False)
    pattern_change_df.to_csv("output/pattern_changes.csv", index=False)

    dist_summary = capital_alloc[capital_alloc.pattern_label.notna()].sort_values("year").groupby("company_id").tail(1)["pattern_label"].value_counts()

    print(f"cashflow_intelligence.xlsx rows: {len(out_df)}")
    print(f"distress_alerts.csv rows: {len(distress_df)}")
    print(f"pattern_changes.csv rows: {len(pattern_change_df)}")
    print("Latest-year capital allocation pattern distribution:")
    print(dist_summary)
    return out_df


if __name__ == "__main__":
    run()
