"""
radar.py
--------
Day 19 deliverable: generates an 8-axis radar chart per company in a
peer group (company's values as filled polygon, peer group average as
dashed overlay), plus a standalone chart for companies with no peer group.

8 axes (all normalized to 0-100 via the same winsorization approach as
Day 17's composite score, for visual comparability):
  ROE, ROCE, NPM, D/E (inverted), FCF score, PAT CAGR 5yr,
  Revenue CAGR 5yr, Composite Score
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "screener"))

from engine import load_screener_universe
from composite_score import (
    compute_scores_for_universe, winsorize_scale, sanitize_known_bad_values,
    KNOWN_BAD_ROE_ROCE_COMPANIES,
)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RADAR_AXES = ["ROE", "ROCE", "NPM", "D/E (inv)", "FCF score", "PAT CAGR 5yr", "Revenue CAGR 5yr", "Composite Score"]
OUT_DIR = "reports/radar_charts"


def build_radar_dataframe():
    """
    Returns the scored universe with 8 new 0-100 columns, one per radar
    axis, ready for plotting. Reuses Day 17's winsorization/sanitization
    so the radar chart's normalization is consistent with the composite
    score's - a company's Composite Score axis and its ROE axis are on
    the exact same scale used to actually compute that composite score.
    """
    df = load_screener_universe()
    df = compute_scores_for_universe(df)  # adds final_composite_score
    df = sanitize_known_bad_values(df)  # nulls ROE/ROCE for known-bad companies
    known_bad_mask = df["company_id"].isin(KNOWN_BAD_ROE_ROCE_COMPANIES)

    df["axis_ROE"] = winsorize_scale(df["return_on_equity_pct"], exclude_from_boundaries=known_bad_mask)
    df["axis_ROCE"] = winsorize_scale(df["return_on_capital_employed_pct"], exclude_from_boundaries=known_bad_mask)
    df["axis_NPM"] = winsorize_scale(df["net_profit_margin_pct"])

    de_raw = winsorize_scale(df["debt_to_equity"])
    df["axis_D/E (inv)"] = de_raw.apply(lambda v: (100 - v) if pd.notna(v) else None)

    df["axis_FCF score"] = df["free_cash_flow_cr"].apply(lambda v: 100.0 if pd.notna(v) and v > 0 else (0.0 if pd.notna(v) else None))
    df["axis_PAT CAGR 5yr"] = winsorize_scale(df["pat_cagr_5yr"])
    df["axis_Revenue CAGR 5yr"] = winsorize_scale(df["revenue_cagr_5yr"])
    df["axis_Composite Score"] = df["final_composite_score"]

    return df


def plot_radar_chart(company_id, company_values, peer_avg_values, peer_group_name, output_path):
    """
    company_values, peer_avg_values: lists of 8 floats (0-100), in the
    same order as RADAR_AXES. NaN values are treated as 0 for plotting
    purposes only (the chart needs a plottable number; the underlying
    data gap is not hidden - it's just visually represented as the axis
    minimum rather than crashing the plot).
    """
    company_values = [0 if pd.isna(v) else v for v in company_values]
    peer_avg_values = [0 if pd.isna(v) else v for v in peer_avg_values]

    n = len(RADAR_AXES)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # close the loop
    company_plot = company_values + company_values[:1]
    peer_plot = peer_avg_values + peer_avg_values[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})

    ax.plot(angles, company_plot, linewidth=2, color="#2563eb", label=company_id)
    ax.fill(angles, company_plot, color="#2563eb", alpha=0.25)

    ax.plot(angles, peer_plot, linewidth=1.5, linestyle="--", color="#6b7280", label=f"{peer_group_name} avg")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(RADAR_AXES, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="gray")

    ax.set_title(f"{company_id} vs {peer_group_name} Average", fontsize=13, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_standalone_chart(company_id, company_values, nifty100_avg_values, output_path):
    """
    For companies with no peer group assigned. Per spec: 'generate a
    single-metric standalone chart with Nifty 100 average as reference'
    - rather than a full 8-axis radar (which implies peer comparison
    that doesn't exist here), this is a simple horizontal bar comparing
    the company's Composite Score against the full 92-company average,
    which is the one metric that summarizes overall quality without
    needing a peer group context.
    """
    company_score = company_values[RADAR_AXES.index("Composite Score")]
    nifty_avg_score = nifty100_avg_values[RADAR_AXES.index("Composite Score")]

    fig, ax = plt.subplots(figsize=(6, 2.5))
    bars = ax.barh(["Nifty 100 Avg", company_id], [nifty_avg_score, company_score],
                    color=["#9ca3af", "#2563eb"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Composite Score (0-100)")
    ax.set_title(f"{company_id} — No Peer Group Assigned\n(Composite Score vs Nifty 100 Average)",
                 fontsize=11, fontweight="bold")

    for bar, value in zip(bars, [nifty_avg_score, company_score]):
        ax.text(value + 1.5, bar.get_y() + bar.get_height() / 2, f"{value:.1f}",
                va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_all_charts(db_path="db/nifty100.db"):
    import sqlite3

    os.makedirs(OUT_DIR, exist_ok=True)

    df = build_radar_dataframe()
    axis_cols = [f"axis_{a}" for a in RADAR_AXES]

    conn = sqlite3.connect(db_path)
    peer_groups = conn.execute("SELECT company_id, peer_group_name FROM peer_groups").fetchall()
    conn.close()
    peer_group_map = {cid: group for cid, group in peer_groups}

    nifty_avg = [df[c].mean() for c in axis_cols]

    generated = 0
    skipped = []

    for _, row in df.iterrows():
        cid = row["company_id"]
        company_values = [row[c] for c in axis_cols]
        # sanitize filename: some tickers contain characters like '&' that
        # are fine in a ticker but awkward in a filename - replace defensively
        safe_cid = cid.replace("&", "AND").replace("/", "-")

        if cid in peer_group_map:
            group_name = peer_group_map[cid]
            peer_members = [c for c, g in peer_group_map.items() if g == group_name]
            peer_df = df[df["company_id"].isin(peer_members)]
            peer_avg = [peer_df[c].mean() for c in axis_cols]

            output_path = os.path.join(OUT_DIR, f"{safe_cid}_radar.png")
            try:
                plot_radar_chart(cid, company_values, peer_avg, group_name, output_path)
                generated += 1
            except Exception as e:
                skipped.append((cid, str(e)))
        else:
            output_path = os.path.join(OUT_DIR, f"{safe_cid}_radar.png")
            try:
                plot_standalone_chart(cid, company_values, nifty_avg, output_path)
                generated += 1
            except Exception as e:
                skipped.append((cid, str(e)))

    return generated, skipped


if __name__ == "__main__":
    generated, skipped = generate_all_charts()
    print(f"Generated {generated} charts in {OUT_DIR}/")
    if skipped:
        print(f"Skipped {len(skipped)} companies due to errors:")
        for cid, err in skipped:
            print(f"  {cid}: {err}")