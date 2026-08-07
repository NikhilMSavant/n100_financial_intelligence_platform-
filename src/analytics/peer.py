"""
peer.py — Sprint 3 / Day 18
Computes PERCENT_RANK for 10 metrics within each of 11 peer groups and
populates peer_percentiles. D/E is inverted so lower D/E -> higher percentile.
"""
import os
import sqlite3
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")

METRICS = [
    "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
    "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr",
    "eps_cagr_5yr", "interest_coverage", "asset_turnover",
]
INVERT = {"debt_to_equity"}  # lower is better -> invert percentile


def latest_ratios(conn):
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    idx = fr.groupby("company_id")["year"].idxmax()
    return fr.loc[idx].reset_index(drop=True)


def compute_peer_percentiles(conn):
    ratios = latest_ratios(conn)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    all_companies = pd.read_sql("SELECT company_id FROM companies", conn)["company_id"]

    rows = []
    for group_name, members in peer_groups.groupby("peer_group_name"):
        member_ids = set(members["company_id"])
        g = ratios[ratios["company_id"].isin(member_ids)]
        for metric in METRICS:
            vals = g[["company_id", "year", metric]].dropna(subset=[metric])
            n = len(vals)
            if n == 0:
                continue
            # PERCENT_RANK equivalent: rank / (n-1), or 1.0 if n==1
            ranked = vals[metric].rank(method="average", pct=False)
            pct_rank = (ranked - 1) / (n - 1) if n > 1 else pd.Series([1.0] * n, index=vals.index)
            if metric in INVERT:
                pct_rank = 1 - pct_rank
            for (_, row), pr in zip(vals.iterrows(), pct_rank):
                rows.append(dict(company_id=row.company_id, peer_group_name=group_name,
                                  metric=metric, value=row[metric], percentile_rank=round(pr, 4),
                                  year=int(row.year)))

    out = pd.DataFrame(rows)

    # Companies not in any peer group
    grouped_ids = set(peer_groups["company_id"])
    unassigned = sorted(set(all_companies) - grouped_ids)

    return out, unassigned


def run():
    conn = sqlite3.connect(DB_PATH)
    out, unassigned = compute_peer_percentiles(conn)
    conn.execute("DELETE FROM peer_percentiles")
    out.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()
    print(f"peer_percentiles populated: {len(out)} rows across "
          f"{out['peer_group_name'].nunique()} peer groups")
    print(f"{len(unassigned)} companies have no peer group assigned "
          f"(message: 'No peer group assigned', no error raised): {unassigned}")

    # spot-check: within IT Services, highest ROE should have highest ROE percentile
    it = out[(out.peer_group_name == "IT Services") & (out.metric == "return_on_equity_pct")]
    if len(it):
        top_roe = it.sort_values("value", ascending=False).iloc[0]
        top_pct = it.sort_values("percentile_rank", ascending=False).iloc[0]
        ok = top_roe["company_id"] == top_pct["company_id"]
        print(f"IT Services spot-check (highest ROE == highest ROE percentile): {ok}")
    conn.close()
    return out, unassigned


if __name__ == "__main__":
    run()
