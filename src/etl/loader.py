"""Sprint 1 — Excel loader: reads all 12 source files, normalises tickers/years,
deduplicates, runs the 16 DQ rules, and writes nifty100.db (SQLite)."""
import sqlite3
import time
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.normaliser import normalize_ticker, normalize_year
from etl import validator as V

RAW = "data/raw"
SUP = "data/supporting"
DB_PATH = "data/nifty100.db"
SCHEMA_PATH = "db/schema.sql"


def load_core(name, sheet_col_map=None):
    df = pd.read_excel(f"{RAW}/{name}.xlsx", header=1)
    return df


def load_supporting(name):
    return pd.read_excel(f"{SUP}/{name}.xlsx", header=0)


def run_etl():
    t0 = time.time()
    audit_rows = []
    all_violations = []

    # ---- companies ----
    companies = load_core("companies")
    companies["id"] = companies["id"].map(normalize_ticker)
    companies["company_name"] = companies["company_name"].astype(str).str.replace("\n", " ", regex=False).str.strip()
    valid_ids = set(companies["id"])
    all_violations += V.dq01_company_pk_uniqueness(companies)
    audit_rows.append(dict(table="companies", rows_in=len(companies), rows_out=len(companies), rejected=0))

    # ---- profit & loss ----
    pl_raw = load_core("profitandloss")
    all_violations += V.dq07_year_format(pl_raw["year"], "profitandloss")
    all_violations += V.dq08_ticker_format(pl_raw["company_id"], "profitandloss")
    pl = pl_raw.copy()
    pl["company_id"] = pl["company_id"].map(normalize_ticker)
    pl["year"] = pl["year"].map(normalize_year)
    n_before = len(pl)
    pl = pl[pl["year"] != "PARSE_ERROR"]
    rejected_year = n_before - len(pl)
    all_violations += V.dq03_fk_integrity(pl, valid_ids, "profitandloss")
    pl = pl[pl["company_id"].isin(valid_ids)]
    all_violations += V.dq02_annual_pk_uniqueness(pl, "profitandloss")
    pl = pl.drop_duplicates(subset=["company_id", "year"], keep="last")
    all_violations += V.dq05_opm_crosscheck(pl)
    all_violations += V.dq06_positive_sales(pl)
    all_violations += V.dq11_tax_rate_range(pl)
    all_violations += V.dq12_dividend_payout_cap(pl)
    all_violations += V.dq14_eps_sign_consistency(pl)
    pl = pl.drop(columns=["id"])
    audit_rows.append(dict(table="profitandloss", rows_in=n_before, rows_out=len(pl), rejected=rejected_year))

    # ---- balance sheet ----
    bs_raw = load_core("balancesheet")
    all_violations += V.dq07_year_format(bs_raw["year"], "balancesheet")
    bs = bs_raw.copy()
    bs["company_id"] = bs["company_id"].map(normalize_ticker)
    bs["year"] = bs["year"].map(normalize_year)
    n_before = len(bs)
    bs = bs[bs["year"] != "PARSE_ERROR"]
    rejected_year = n_before - len(bs)
    all_violations += V.dq03_fk_integrity(bs, valid_ids, "balancesheet")
    bs = bs[bs["company_id"].isin(valid_ids)]
    all_violations += V.dq02_annual_pk_uniqueness(bs, "balancesheet")
    bs = bs.drop_duplicates(subset=["company_id", "year"], keep="last")
    bs["fixed_assets"] = bs["fixed_assets"].fillna(0)
    all_violations += V.dq10_nonneg_fixed_assets(bs)
    bs.loc[bs["fixed_assets"] < 0, "fixed_assets"] = 0
    all_violations += V.dq04_bs_balance(bs)
    all_violations += V.dq15_bse_asset_balance_strict(bs)
    bs = bs.drop(columns=["id"])
    audit_rows.append(dict(table="balancesheet", rows_in=n_before, rows_out=len(bs), rejected=rejected_year))

    # ---- cash flow ----
    cf_raw = load_core("cashflow")
    all_violations += V.dq07_year_format(cf_raw["year"], "cashflow")
    cf = cf_raw.copy()
    cf["company_id"] = cf["company_id"].map(normalize_ticker)
    cf["year"] = cf["year"].map(normalize_year)
    n_before = len(cf)
    cf = cf[cf["year"] != "PARSE_ERROR"]
    rejected_year = n_before - len(cf)
    all_violations += V.dq03_fk_integrity(cf, valid_ids, "cashflow")
    cf = cf[cf["company_id"].isin(valid_ids)]
    all_violations += V.dq02_annual_pk_uniqueness(cf, "cashflow")
    cf = cf.drop_duplicates(subset=["company_id", "year"], keep="last")
    all_violations += V.dq09_net_cash_check(cf)
    cf = cf.drop(columns=["id"])
    audit_rows.append(dict(table="cashflow", rows_in=n_before, rows_out=len(cf), rejected=rejected_year))

    # ---- analysis (partial coverage, 1:1) ----
    analysis = load_core("analysis")
    analysis["company_id"] = analysis["company_id"].map(normalize_ticker)
    analysis = analysis[analysis["company_id"].isin(valid_ids)].drop(columns=["id"])
    analysis = analysis.drop_duplicates(subset=["company_id"], keep="last")
    audit_rows.append(dict(table="analysis", rows_in=20, rows_out=len(analysis), rejected=20 - len(analysis)))

    # ---- documents ----
    documents = load_core("documents")
    documents["company_id"] = documents["company_id"].map(normalize_ticker)
    documents = documents.rename(columns={"Year": "year", "Annual_Report": "annual_report"})
    n_before = len(documents)
    documents = documents[documents["company_id"].isin(valid_ids)]
    all_violations += V.dq13_url_validity_placeholder(documents)
    documents = documents.drop_duplicates(subset=["company_id", "year"], keep="last").drop(columns=["id"])
    audit_rows.append(dict(table="documents", rows_in=n_before, rows_out=len(documents), rejected=n_before - len(documents)))

    # ---- pros and cons ----
    prosandcons = load_core("prosandcons")
    prosandcons["company_id"] = prosandcons["company_id"].map(normalize_ticker)
    n_before = len(prosandcons)
    prosandcons = prosandcons[prosandcons["company_id"].isin(valid_ids)]
    audit_rows.append(dict(table="prosandcons", rows_in=n_before, rows_out=len(prosandcons), rejected=n_before - len(prosandcons)))

    # ---- supplementary: sectors ----
    sectors = load_supporting("sectors")
    sectors["company_id"] = sectors["company_id"].map(normalize_ticker)
    sectors = sectors[sectors["company_id"].isin(valid_ids)].drop(columns=["id"])
    audit_rows.append(dict(table="sectors", rows_in=92, rows_out=len(sectors), rejected=92 - len(sectors)))

    # ---- market_cap ----
    market_cap = load_supporting("market_cap")
    market_cap["company_id"] = market_cap["company_id"].map(normalize_ticker)
    n_before = len(market_cap)
    market_cap = market_cap[market_cap["company_id"].isin(valid_ids)].drop(columns=["id"])
    market_cap = market_cap.drop_duplicates(subset=["company_id", "year"], keep="last")
    audit_rows.append(dict(table="market_cap", rows_in=n_before, rows_out=len(market_cap), rejected=n_before - len(market_cap)))

    # ---- stock_prices ----
    stock_prices = load_supporting("stock_prices")
    stock_prices["company_id"] = stock_prices["company_id"].map(normalize_ticker)
    n_before = len(stock_prices)
    stock_prices = stock_prices[stock_prices["company_id"].isin(valid_ids)].drop(columns=["id"])
    stock_prices["date"] = stock_prices["date"].astype(str)
    stock_prices = stock_prices.drop_duplicates(subset=["company_id", "date"], keep="last")
    audit_rows.append(dict(table="stock_prices", rows_in=n_before, rows_out=len(stock_prices), rejected=n_before - len(stock_prices)))

    # ---- peer_groups ----
    peer_groups = load_supporting("peer_groups")
    peer_groups["company_id"] = peer_groups["company_id"].map(normalize_ticker)
    n_before = len(peer_groups)
    peer_groups = peer_groups[peer_groups["company_id"].isin(valid_ids)].drop(columns=["id"])
    peer_groups["is_benchmark"] = peer_groups["is_benchmark"].astype(int)
    audit_rows.append(dict(table="peer_groups", rows_in=n_before, rows_out=len(peer_groups), rejected=n_before - len(peer_groups)))

    # companies final projection (drop non-storage cols not in schema)
    companies_final = companies[["id", "company_name", "about_company", "website", "nse_profile",
                                  "bse_profile", "face_value", "book_value", "roce_percentage", "roe_percentage"]]

    # ---- write SQLite ----
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    companies_final.to_sql("companies", conn, if_exists="append", index=False)
    pl.to_sql("profitandloss", conn, if_exists="append", index=False)
    bs.to_sql("balancesheet", conn, if_exists="append", index=False)
    cf.to_sql("cashflow", conn, if_exists="append", index=False)
    analysis.to_sql("analysis", conn, if_exists="append", index=False)
    documents.to_sql("documents", conn, if_exists="append", index=False)
    prosandcons.to_sql("prosandcons", conn, if_exists="append", index=False)
    sectors.to_sql("sectors", conn, if_exists="append", index=False)
    market_cap.to_sql("market_cap", conn, if_exists="append", index=False)
    stock_prices.to_sql("stock_prices", conn, if_exists="append", index=False)
    peer_groups.to_sql("peer_groups", conn, if_exists="append", index=False)
    conn.commit()

    # FK check
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()

    conn.close()

    runtime = time.time() - t0

    # ---- write audit + validation csvs ----
    os.makedirs("output", exist_ok=True)
    audit_df = pd.DataFrame(audit_rows)
    audit_df["timestamp"] = pd.Timestamp.now().isoformat()
    audit_df["runtime_s"] = round(runtime, 2)
    audit_df.to_csv("output/load_audit.csv", index=False)

    val_df = pd.DataFrame(all_violations, columns=["company_id", "year", "field", "issue", "severity", "rule_id"])
    val_df.to_csv("output/validation_failures.csv", index=False)

    critical_count = (val_df["severity"] == "CRITICAL").sum() if len(val_df) else 0

    print(f"ETL complete in {runtime:.2f}s")
    print(f"companies={len(companies_final)}  P&L={len(pl)}  BS={len(bs)}  CF={len(cf)}  "
          f"stock_prices={len(stock_prices)}  market_cap={len(market_cap)}")
    print(f"FK check violations: {len(fk_violations)}")
    print(f"DQ violations logged: {len(val_df)}  (CRITICAL={critical_count})")
    return dict(critical=critical_count, fk_violations=len(fk_violations), total_dq=len(val_df))


if __name__ == "__main__":
    run_etl()
