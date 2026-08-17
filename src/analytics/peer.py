"""Sprint 3 Day 18 — peer percentile computation: PERCENT_RANK for 10 metrics
within each of the peer groups defined in peer_groups.xlsx."""
import sys
import pathlib
import sqlite3
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from screener.engine import load_latest_universe

METRICS = [
    ("return_on_equity_pct", False),
    ("return_on_capital_employed_pct", False),
    ("net_profit_margin_pct", False),
    ("debt_to_equity", True),           # inverse — lower D/E = higher percentile
    ("free_cash_flow_cr", False),
    ("pat_cagr_5yr", False),
    ("revenue_cagr_5yr", False),
    ("eps_cagr_5yr", False),
    ("interest_coverage", False),
    ("asset_turnover", False),
]


def run_peer_percentiles():
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()

    covered_ids = set(peer_groups["company_id"])
    universe["has_peer_group"] = universe["company_id"].isin(covered_ids)

    rows = []
    for group_name, members in peer_groups.groupby("peer_group_name"):
        member_ids = members["company_id"].tolist()
        grp_df = universe[universe["company_id"].isin(member_ids)]
        for metric, invert in METRICS:
            valid = grp_df[["company_id", "year", metric]].dropna(subset=[metric])
            if valid.empty:
                continue
            pct = valid[metric].rank(pct=True, method="average")
            if invert:
                pct = 1 - pct
            for (_, r), p in zip(valid.iterrows(), pct):
                rows.append(dict(company_id=r["company_id"], peer_group_name=group_name,
                                  metric=metric, value=r[metric], percentile_rank=round(float(p), 4),
                                  year=r["year"]))

    percentiles_df = pd.DataFrame(rows)

    conn = sqlite3.connect("data/nifty100.db")
    conn.execute("DELETE FROM peer_percentiles")
    percentiles_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    print(f"peer_percentiles rows: {len(percentiles_df)}")
    print(f"peer groups covered: {percentiles_df['peer_group_name'].nunique()}")

    no_group = universe[~universe["has_peer_group"]]["company_id"].tolist()
    print(f"companies with 'No peer group assigned': {len(no_group)}")
    return percentiles_df, no_group


if __name__ == "__main__":
    run_peer_percentiles()
