"""
radar.py — Sprint 3 / Day 19
Generates an 8-axis radar chart per company (company polygon filled, peer
group average as dashed outline), exported as PNG to reports/radar_charts/.
Companies with no peer group get a standalone chart vs the Nifty-100 average.
"""
import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "reports", "radar_charts")

AXES = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr",
        "composite_quality_score"]
AXES_LABELS = ["ROE", "ROCE", "NPM", "D/E", "FCF score", "PAT CAGR 5yr", "Rev CAGR 5yr", "Composite"]


def _normalise(df, cols):
    """0-100 min-max scale each axis across the full universe so radar shapes are comparable.
    D/E is inverted (lower D/E = better = higher score)."""
    out = df.copy()
    for c in cols:
        s = out[c].astype(float)
        lo, hi = s.min(), s.max()
        if hi == lo:
            out[c + "_n"] = 50.0
            continue
        scaled = (s - lo) / (hi - lo) * 100
        if c == "debt_to_equity":
            scaled = 100 - scaled
        out[c + "_n"] = scaled.fillna(scaled.median())
    return out


def _plot(company_row, avg_values, title, out_path):
    n = len(AXES)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    company_vals = [company_row[c + "_n"] for c in AXES] + [company_row[AXES[0] + "_n"]]
    avg_vals = list(avg_values) + [avg_values[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, company_vals, color="#1f77b4", linewidth=2)
    ax.fill(angles, company_vals, color="#1f77b4", alpha=0.25)
    ax.plot(angles, avg_vals, color="#888888", linewidth=1.5, linestyle="--")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXES_LABELS, fontsize=9)
    ax.set_yticklabels([])
    ax.set_title(title, fontsize=12, pad=20)
    ax.legend(["Company", "Peer group avg"], loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def run(limit=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    idx = fr.groupby("company_id")["year"].idxmax()
    latest = fr.loc[idx].reset_index(drop=True)
    latest = _normalise(latest, AXES)
    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    latest = latest.merge(companies, on="company_id", how="left")

    grouped_ids = set(peer_groups.company_id)
    nifty_avg = [latest[c + "_n"].mean() for c in AXES]

    n_written = 0
    ids = latest["company_id"].tolist() if limit is None else latest["company_id"].tolist()[:limit]
    for cid in ids:
        row = latest[latest.company_id == cid].iloc[0]
        pg = peer_groups[peer_groups.company_id == cid]
        if len(pg):
            group_name = pg.iloc[0]["peer_group_name"]
            member_ids = peer_groups[peer_groups.peer_group_name == group_name]["company_id"]
            group_df = latest[latest.company_id.isin(member_ids)]
            avg_vals = [group_df[c + "_n"].mean() for c in AXES]
            title = f"{row.company_name} ({cid}) vs {group_name} avg"
        else:
            avg_vals = nifty_avg
            title = f"{row.company_name} ({cid}) vs Nifty 100 avg"
        out_path = os.path.join(OUT_DIR, f"{cid}_radar.png")
        _plot(row, avg_vals, title, out_path)
        n_written += 1

    print(f"Radar charts written: {n_written} -> {OUT_DIR}")
    conn.close()


if __name__ == "__main__":
    run()
