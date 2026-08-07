"""
engine.py — Sprint 3 / Day 15-16
Loads screener_config.yaml, joins financial_ratios + sectors + market_cap +
profitandloss into one analysis frame, and applies threshold filters /
preset screeners against it.
"""
import os
import sqlite3
import yaml
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
CONFIG_PATH = os.path.join(ROOT, "config", "screener_config.yaml")


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def build_universe(conn, latest_only=True):
    """One row per company (latest available fiscal year), with ratios + valuation + sector joined."""
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    if latest_only:
        idx = fr.groupby("company_id")["year"].idxmax()
        fr = fr.loc[idx].reset_index(drop=True)

    sectors = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)
    pl = pd.read_sql("SELECT company_id, year, sales, net_profit, dividend_payout FROM profitandloss", conn)
    mc = pd.read_sql("SELECT * FROM market_cap", conn)
    mc_idx = mc.groupby("company_id")["year"].idxmax()
    mc_latest = mc.loc[mc_idx].reset_index(drop=True)

    df = fr.merge(companies, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(pl, on=["company_id", "year"], how="left", suffixes=("", "_pl"))
    df = df.merge(mc_latest.drop(columns=["year"]), on="company_id", how="left")

    # D/E declining YoY (needed for Turnaround Watch preset)
    fr_all = pd.read_sql("SELECT company_id, year, debt_to_equity, free_cash_flow_cr, "
                          "revenue_cagr_3yr FROM financial_ratios", conn).sort_values(["company_id", "year"])
    fr_all["de_prev"] = fr_all.groupby("company_id")["debt_to_equity"].shift(1)
    fr_all["de_declining"] = fr_all["debt_to_equity"] < fr_all["de_prev"]
    latest_de = fr_all.loc[fr_all.groupby("company_id")["year"].idxmax(), ["company_id", "de_declining"]]
    df = df.merge(latest_de, on="company_id", how="left")

    return df


def apply_filters(df, filters, config):
    """filters: dict of metric_key -> threshold value, using config['metrics'] mapping."""
    metrics = config["metrics"]
    out = df.copy()
    for key, threshold in filters.items():
        if key == "de_declining_yoy":
            if threshold:
                out = out[out["de_declining"] == True]  # noqa: E712
            continue
        if key == "dividend_payout_max":
            out = out[out["dividend_payout_ratio_pct"].fillna(999) <= threshold]
            continue
        if key not in metrics:
            continue
        col = metrics[key]["column"]
        direction = metrics[key]["direction"]
        if col not in out.columns:
            continue
        if key == "de_max":
            # D/E filter: auto-skip Financials sector (structurally high leverage is normal)
            mask_fin = out["broad_sector"] == "Financials"
            mask_pass = out[col] <= threshold
            out = out[mask_fin | mask_pass]
            continue
        if key == "icr_min":
            # Debt Free (ICR label, value None) always passes any ICR minimum
            mask_debtfree = out["icr_label"] == "Debt Free"
            mask_pass = out[col] >= threshold
            out = out[mask_debtfree | mask_pass]
            continue
        if direction == "min":
            out = out[out[col].fillna(-1e18) >= threshold]
        else:
            out = out[out[col].fillna(1e18) <= threshold]
    return out


def run_preset(df, preset_key, config):
    preset = config["presets"][preset_key]
    result = apply_filters(df, preset["filters"], config)
    result = result.sort_values("composite_quality_score", ascending=False)
    return preset["label"], result


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    config = load_config()
    universe = build_universe(conn)
    print(f"Universe size: {len(universe)} companies")
    for key in config["presets"]:
        label, result = run_preset(universe, key, config)
        print(f"{label}: {len(result)} companies")
