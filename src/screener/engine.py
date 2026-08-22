"""Sprint 3 — Filter engine: loads screener_config.yaml, applies threshold
filters to the financial_ratios (+ market_cap) DataFrame, and runs the 6
preset screeners."""
import sys
import pathlib
import sqlite3
import yaml
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from analytics.scoring import compute_composite_score

DB_PATH = "data/nifty100.db"
CONFIG_PATH = "config/screener_config.yaml"


def load_latest_universe(conn):
    """One row per company: latest-year financial_ratios + latest market_cap + sector + company name."""
    # Only consider years with a real P&L (net_profit_margin present) as candidates for "latest" —
    # excludes interim/partial balance-sheet-only snapshots (e.g. half-year BS updates with no matching P&L).
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE net_profit_margin_pct IS NOT NULL", conn)
    ratios = ratios.sort_values(["company_id", "year"]).groupby("company_id").tail(1).reset_index(drop=True)

    mcap = pd.read_sql("SELECT * FROM market_cap", conn)
    mcap_latest = mcap.sort_values(["company_id", "year"]).groupby("company_id").tail(1).reset_index(drop=True)
    mcap_latest = mcap_latest.rename(columns={"year": "mcap_year"})

    sectors = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    pl_latest = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    pl_latest = pl_latest.sort_values(["company_id", "year"]).groupby("company_id").tail(1).reset_index(drop=True)

    df = ratios.merge(mcap_latest, on="company_id", how="left") \
               .merge(sectors, on="company_id", how="left") \
               .merge(companies, on="company_id", how="left") \
               .merge(pl_latest[["company_id", "sales", "net_profit"]], on="company_id", how="left")

    df["fcf_yield_pct"] = np.where(df["market_cap_crore"] > 0,
                                    df["free_cash_flow_cr"] / df["market_cap_crore"] * 100, np.nan)
    df["composite_quality_score"] = compute_composite_score(df, sector_relative=False)
    df["composite_quality_score_sector_relative"] = compute_composite_score(df, sector_relative=True)
    return df


def _passes(row, field, cond, config):
    val = row.get(field)
    if (field == "debt_to_equity" and config.get("de_filter_skip_sector")
            and row.get("broad_sector") == config["de_filter_skip_sector"] and "equals" not in cond):
        return True  # D/E max-threshold filter skipped for Financials sector — NOT for an exact-equals condition
    if field == "interest_coverage" and row.get("icr_label") == "Debt Free":
        return True  # Debt Free treated as ICR = infinity -> passes any minimum
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return False
    if "min" in cond and val < cond["min"]:
        return False
    if "max" in cond and val > cond["max"]:
        return False
    if "equals" in cond and val != cond["equals"]:
        return False
    return True


def apply_filters(df: pd.DataFrame, filters: dict, config: dict) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for field, cond in filters.items():
        mask &= df.apply(lambda r: _passes(r, field, cond, config), axis=1)
    return df[mask]


def turnaround_watch(df: pd.DataFrame, conn) -> pd.DataFrame:
    """Special preset: Revenue CAGR 3yr > 10%, FCF positive latest year, D/E declining YoY."""
    base = df[(df["revenue_cagr_3yr"] > 10) & (df["free_cash_flow_cr"] > 0)]
    ratios_all = pd.read_sql("SELECT company_id, year, debt_to_equity FROM financial_ratios", conn)
    declining = []
    for cid in base["company_id"]:
        g = ratios_all[ratios_all.company_id == cid].sort_values("year")
        if len(g) >= 2 and pd.notna(g["debt_to_equity"].iloc[-1]) and pd.notna(g["debt_to_equity"].iloc[-2]):
            if g["debt_to_equity"].iloc[-1] < g["debt_to_equity"].iloc[-2]:
                declining.append(cid)
    return base[base["company_id"].isin(declining)]


def run_screener():
    conn = sqlite3.connect(DB_PATH)
    df = load_latest_universe(conn)
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    results = {}
    for key, preset in config["presets"].items():
        if key == "turnaround_watch":
            res = turnaround_watch(df, conn)
        else:
            res = apply_filters(df, preset["filters"], config)
        rank_col = preset["rank_by"]
        if rank_col in res.columns:
            res = res.sort_values(rank_col, ascending=False)
        results[key] = res
        lo, hi = preset["expected_range"]
        status = "OK" if lo <= len(res) <= hi else "OUT_OF_RANGE"
        print(f"{preset['label']}: {len(res)} companies (expected {lo}-{hi}) [{status}]")
    conn.close()
    return df, results, config


if __name__ == "__main__":
    run_screener()
