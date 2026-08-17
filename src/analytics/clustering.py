"""Sprint 6 Day 36-37 — KMeans clustering (5 clusters), elbow plot,
correlation heatmap, outlier detection, portfolio statistics."""
import sys
import pathlib
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from screener.engine import load_latest_universe

FEATURES = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr",
            "operating_profit_margin_pct"]
# free_cash_flow_cr used as proxy for fcf_cagr_5yr (5yr FCF CAGR isn't a stored per-row column in this schema)


def prep_features(universe: pd.DataFrame):
    df = universe.copy()
    for col in FEATURES:
        df[col] = df.groupby("broad_sector")[col].transform(lambda s: s.fillna(s.median()))
        df[col] = df[col].fillna(df[col].median())  # residual fallback for sectors with all-NaN
        # Winsorize at P5/P95 before scaling — a handful of near-zero-equity companies (e.g. BEL, HAL)
        # produce ROE in the thousands of percent and would otherwise dominate the Euclidean distance.
        # (P1/P99 is too weak to matter with only 92 companies in the universe.)
        lo, hi = df[col].quantile(0.05), df[col].quantile(0.95)
        df[col] = df[col].clip(lo, hi)
    return df


def elbow_plot(X_scaled, out_path):
    inertias = []
    for k in range(2, 11):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled)
        inertias.append(km.inertia_)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(range(2, 11), inertias, marker="o")
    ax.axvline(5, color="red", linestyle="--", label="k=5 (chosen)")
    ax.set_xlabel("k"); ax.set_ylabel("Inertia"); ax.set_title("KMeans Elbow Plot")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def name_clusters(profile: pd.DataFrame):
    """Rank the 5 cluster centroids by a composite quality axis and assign
    5 distinct descriptive names (rank-based, so no two clusters collapse
    onto the same label)."""
    ranked = profile.copy()
    ranked["_score"] = (
        ranked["return_on_equity_pct"].rank()
        + ranked["revenue_cagr_5yr"].rank()
        + ranked["operating_profit_margin_pct"].rank()
        - ranked["debt_to_equity"].rank()
    )
    order = ranked.sort_values("_score", ascending=False).index.tolist()  # best -> worst
    label_sequence = ["High-Quality Compounders", "Emerging Growth", "Defensive Dividend Payers",
                       "Value Cyclicals", "Distressed or Turnaround"]
    # The worst-ranked cluster is only relabelled 'Distressed or Turnaround' if its centroid
    # actually shows negative ROE or negative revenue growth; otherwise all 5 clusters keep
    # distinct names in rank order even though none qualifies as distressed in this universe.
    worst = order[-1]
    if not (profile.loc[worst, "return_on_equity_pct"] < 0 or profile.loc[worst, "revenue_cagr_5yr"] < 0):
        label_sequence[-1] = "Turnaround Watch"
    return {cid: label for cid, label in zip(order, label_sequence)}


def run_clustering():
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    conn.close()

    df = prep_features(universe)
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pathlib.Path("reports").mkdir(exist_ok=True)
    elbow_plot(X_scaled, "reports/elbow_plot.png")

    km = KMeans(n_clusters=5, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    distances = np.linalg.norm(X_scaled - km.cluster_centers_[labels], axis=1)

    df["cluster_id"] = labels
    df["distance_from_centroid"] = distances

    profile = df.groupby("cluster_id")[FEATURES].mean()
    names = name_clusters(profile)
    df["cluster_name"] = df["cluster_id"].map(names)

    out = df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]]
    pathlib.Path("output").mkdir(exist_ok=True)
    out.to_csv("output/cluster_labels.csv", index=False)

    print("Cluster profile (mean of input features):")
    print(profile.assign(cluster_name=profile.index.map(names)))
    print(f"\ncluster_labels.csv rows: {len(out)}  (all 92: {len(out) == 92})")
    return df, profile


def correlation_heatmap():
    import seaborn as sns  # optional; fall back to matplotlib imshow if unavailable
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    conn.close()
    kpi_cols = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
                "debt_to_equity", "interest_coverage", "asset_turnover", "free_cash_flow_cr",
                "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr"]
    corr = universe[kpi_cols].corr(method="pearson")
    fig, ax = plt.subplots(figsize=(9, 7))
    try:
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, annot_kws={"size": 6})
    except Exception:
        im = ax.imshow(corr, cmap="coolwarm")
        ax.set_xticks(range(len(kpi_cols))); ax.set_xticklabels(kpi_cols, rotation=90, fontsize=6)
        ax.set_yticks(range(len(kpi_cols))); ax.set_yticklabels(kpi_cols, fontsize=6)
        fig.colorbar(im)
    fig.tight_layout()
    fig.savefig("reports/correlation_heatmap.png", dpi=120)
    plt.close(fig)
    print("Saved reports/correlation_heatmap.png")


def outlier_detection():
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    conn.close()
    metrics = ["return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct", "revenue_cagr_5yr",
               "pat_cagr_5yr", "asset_turnover"]
    rows = []
    for sector, grp in universe.groupby("broad_sector"):
        for m in metrics:
            mean, std = grp[m].mean(), grp[m].std()
            if not std or pd.isna(std):
                continue
            z = (grp[m] - mean) / std
            outliers = grp[abs(z) > 3]
            for _, r in outliers.iterrows():
                rows.append(dict(company_id=r["company_id"], metric=m, value=r[m],
                                  z_score=round(float((r[m] - mean) / std), 2), sector=sector,
                                  sector_mean=round(mean, 2), sector_std=round(std, 2)))
    pd.DataFrame(rows).to_csv("output/outlier_report.csv", index=False)
    print(f"outlier_report.csv rows: {len(rows)}")


def portfolio_stats():
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    conn.close()
    kpi_cols = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
                "debt_to_equity", "interest_coverage", "asset_turnover", "free_cash_flow_cr",
                "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr"]
    stats = []
    for c in kpi_cols:
        s = universe[c].dropna()
        stats.append(dict(metric=c, P10=s.quantile(.10), P25=s.quantile(.25), P50=s.quantile(.50),
                           P75=s.quantile(.75), P90=s.quantile(.90), Mean=s.mean(), Std=s.std()))
    pd.DataFrame(stats).round(2).to_csv("output/portfolio_stats.csv", index=False)
    print("portfolio_stats.csv written")


if __name__ == "__main__":
    run_clustering()
    correlation_heatmap()
    outlier_detection()
    portfolio_stats()
