"""
loader.py — Sprint 1 / Day 02 & 05
Loads the 7 core + 5 supplementary Excel workbooks into nifty100.db,
in FK-safe order, and writes output/load_audit.csv.
"""
import os
import sqlite3
import pandas as pd

import sys
sys.path.insert(0, os.path.dirname(__file__))
from normaliser import normalize_year, normalize_ticker, normalize_numeric, is_ttm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_SUPP = os.path.join(ROOT, "data", "supplementary")
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
SCHEMA_PATH = os.path.join(ROOT, "db", "schema.sql")
OUT_DIR = os.path.join(ROOT, "output")


def _read(path, header=1):
    return pd.read_excel(path, header=header)


def build_schema(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()


def load_companies(conn, audit):
    df = _read(os.path.join(DATA_RAW, "companies.xlsx"))
    df = df.rename(columns={"id": "company_id"})
    df["company_id"] = df["company_id"].map(normalize_ticker)
    out = df[["company_id", "company_name", "about_company", "website",
              "nse_profile", "bse_profile", "face_value", "book_value",
              "roce_percentage", "roe_percentage"]].drop_duplicates("company_id")
    out.to_sql("companies", conn, if_exists="append", index=False)
    audit.append(("companies", len(df), len(out), len(df) - len(out)))
    return set(out["company_id"])


def load_sectors(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_SUPP, "sectors.xlsx"))
    df["company_id"] = df["company_id"].map(normalize_ticker)
    df = df[df["company_id"].isin(valid_ids)]
    out = df[["company_id", "broad_sector", "sub_sector", "index_weight_pct",
              "market_cap_category"]].drop_duplicates("company_id")
    out.to_sql("sectors", conn, if_exists="append", index=False)
    audit.append(("sectors", len(df), len(out), 0))


def _load_year_table(conn, audit, filename, table, value_cols, valid_ids, header=1):
    df = _read(os.path.join(DATA_RAW, filename), header=header)
    df["company_id"] = df["company_id"].map(normalize_ticker)
    df["fy_year"] = df["year"].map(normalize_year)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    df = df[df["fy_year"].notna()]  # drop TTM / unparsable rows
    for c in value_cols:
        if c in df.columns:
            df[c] = df[c].map(normalize_numeric)
    df = df.drop(columns=["year"]).rename(columns={"fy_year": "year"})
    df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
    out_cols = ["company_id", "year"] + value_cols
    out = df[out_cols]
    # Drop placeholder "shell" rows where every reported value column is 0/NaN
    # (seen e.g. for ADANIENSOL Mar-2014, a pre-listing filler row with sales=0,
    # total_assets=0 -- CRITICAL DQ-06/DQ-07 exception, resolved by exclusion
    # rather than fabricating data; documented in output/known_exceptions.md)
    all_zero = (out[value_cols].fillna(0) == 0).all(axis=1)
    out = out[~all_zero]
    # Shell/pre-listing rows can also show near-zero totals with one stray non-zero
    # cell (e.g. ADANIENSOL Mar-2014 has equity_capital=0.1 but sales=0 and
    # total_assets=0) -- exclude on the anchor fields directly for PL/BS.
    if "sales" in value_cols:
        out = out[out["sales"] != 0]
    if "total_assets" in value_cols:
        out = out[out["total_assets"] != 0]
    out.to_sql(table, conn, if_exists="append", index=False)
    audit.append((table, n_in, len(out), n_in - len(out)))


def load_analysis(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_RAW, "analysis.xlsx"), header=1)
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    out = df.rename(columns={
        "id": "id",
        "compounded_sales_growth": "compounded_sales_growth_raw",
        "compounded_profit_growth": "compounded_profit_growth_raw",
        "stock_price_cagr": "stock_price_cagr_raw",
        "roe": "roe_raw",
    })[["id", "company_id", "compounded_sales_growth_raw", "compounded_profit_growth_raw",
        "stock_price_cagr_raw", "roe_raw"]]
    out.to_sql("analysis", conn, if_exists="append", index=False)
    audit.append(("analysis", n_in, len(out), n_in - len(out)))


def load_documents(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_RAW, "documents.xlsx"), header=1)
    df = df.rename(columns={"Year": "year", "Annual_Report": "annual_report"})
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
    out = df[["company_id", "year", "annual_report"]]
    out.to_sql("documents", conn, if_exists="append", index=False)
    audit.append(("documents", n_in, len(out), n_in - len(out)))


def load_prosandcons(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_RAW, "prosandcons.xlsx"), header=1)
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    out = df.rename(columns={"id": "id"})[["id", "company_id", "pros", "cons"]]
    out.to_sql("prosandcons", conn, if_exists="append", index=False)
    audit.append(("prosandcons", n_in, len(out), n_in - len(out)))


def load_stock_prices(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_SUPP, "stock_prices.xlsx"))
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    out = df[["id", "company_id", "date", "open_price", "high_price", "low_price",
              "close_price", "volume", "adjusted_close"]]
    out.to_sql("stock_prices", conn, if_exists="append", index=False)
    audit.append(("stock_prices", n_in, len(out), n_in - len(out)))


def load_market_cap(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_SUPP, "market_cap.xlsx"))
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    out = df[["company_id", "year", "market_cap_crore", "enterprise_value_crore",
              "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]]
    out.to_sql("market_cap", conn, if_exists="append", index=False)
    audit.append(("market_cap", n_in, len(out), n_in - len(out)))


def load_peer_groups(conn, audit, valid_ids):
    df = pd.read_excel(os.path.join(DATA_SUPP, "peer_groups.xlsx"))
    df["company_id"] = df["company_id"].map(normalize_ticker)
    n_in = len(df)
    df = df[df["company_id"].isin(valid_ids)]
    out = df[["id", "peer_group_name", "company_id", "is_benchmark"]]
    out.to_sql("peer_groups", conn, if_exists="append", index=False)
    audit.append(("peer_groups", n_in, len(out), n_in - len(out)))


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    build_schema(conn)

    audit = []
    valid_ids = load_companies(conn, audit)
    load_sectors(conn, audit, valid_ids)
    _load_year_table(conn, audit, "profitandloss.xlsx", "profitandloss",
                      ["sales", "expenses", "operating_profit", "opm_percentage",
                       "other_income", "interest", "depreciation", "profit_before_tax",
                       "tax_percentage", "net_profit", "eps", "dividend_payout"], valid_ids)
    _load_year_table(conn, audit, "balancesheet.xlsx", "balancesheet",
                      ["equity_capital", "reserves", "borrowings", "other_liabilities",
                       "total_liabilities", "fixed_assets", "cwip", "investments",
                       "other_asset", "total_assets"], valid_ids)
    _load_year_table(conn, audit, "cashflow.xlsx", "cashflow",
                      ["operating_activity", "investing_activity", "financing_activity",
                       "net_cash_flow"], valid_ids)
    load_analysis(conn, audit, valid_ids)
    load_documents(conn, audit, valid_ids)
    load_prosandcons(conn, audit, valid_ids)
    load_stock_prices(conn, audit, valid_ids)
    load_market_cap(conn, audit, valid_ids)
    load_peer_groups(conn, audit, valid_ids)
    conn.commit()

    fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()

    audit_df = pd.DataFrame(audit, columns=["table", "rows_in_source", "rows_loaded", "rows_rejected"])
    audit_df.to_csv(os.path.join(OUT_DIR, "load_audit.csv"), index=False)

    print(audit_df.to_string(index=False))
    print(f"\nPRAGMA foreign_key_check -> {len(fk_issues)} violation rows")
    print(f"companies count = {conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0]}")
    conn.close()
    return audit_df, fk_issues


if __name__ == "__main__":
    run()
