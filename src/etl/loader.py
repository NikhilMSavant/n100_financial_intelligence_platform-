"""
loader.py
---------
Day 4-5 deliverable: loads all 12 source Excel files into nifty100.db,
applying normalize_year() / normalize_ticker() from normaliser.py.

Produces:
  - db/nifty100.db
  - output/load_audit.csv   (per-table row counts, rejects, load status)

Run with: python src/etl/loader.py
"""
import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from normaliser import normalize_year, normalize_ticker

RAW_DIR = "data/raw"
SUPP_DIR = "data/supplementary"
DB_PATH = "db/nifty100.db"
SCHEMA_PATH = "db/schema.sql"
AUDIT_PATH = "output/load_audit.csv"

# (file_stem, folder, header_row) — core files have a merged title row at 0
CORE_FILES = [
    ("companies", RAW_DIR, 1),
    ("profitandloss", RAW_DIR, 1),
    ("balancesheet", RAW_DIR, 1),
    ("cashflow", RAW_DIR, 1),
    ("analysis", RAW_DIR, 1),
    ("documents", RAW_DIR, 1),
    ("prosandcons", RAW_DIR, 1),
]
SUPP_FILES = [
    ("sectors", SUPP_DIR, 0),
    ("stock_prices", SUPP_DIR, 0),
    ("market_cap", SUPP_DIR, 0),
    ("financial_ratios", SUPP_DIR, 0),
    ("peer_groups", SUPP_DIR, 0),
]

# Tables that have a 'year' column needing normalize_year()
YEAR_TABLES = {
    "profitandloss": "year",
    "balancesheet": "year",
    "cashflow": "year",
    "documents": "Year",       # capital Y in source
    "market_cap": "year",
    "financial_ratios": "year",
}

# Every table except 'companies' has company_id needing normalize_ticker()
COMPANY_ID_COL = "company_id"

# Composite key each table must be unique on (DQ-01 / DQ-02). Exact-duplicate
# rows found in the raw data (e.g. ASIANPAINT/ADANIPORTS repeated in
# balancesheet/profitandloss/cashflow/financial_ratios) are quarantined here:
# first occurrence kept, rest rejected and counted in load_audit.csv.
PK_COLUMNS = {
    "profitandloss": ["company_id", "year"],
    "balancesheet": ["company_id", "year"],
    "cashflow": ["company_id", "year"],
    "market_cap": ["company_id", "year"],
    "financial_ratios": ["company_id", "year"],
    "stock_prices": ["company_id", "date"],
    "sectors": ["company_id"],
}

audit_rows = []
dupe_report_rows = []
fk_orphan_rows = []


def log_audit(table, source_rows, loaded_rows, rejected_rows, status, note=""):
    audit_rows.append({
        "table": table,
        "source_rows": source_rows,
        "loaded_rows": loaded_rows,
        "rejected_rows": rejected_rows,
        "status": status,
        "note": note,
        "loaded_at": datetime.now().isoformat(timespec="seconds"),
    })


def load_dataframe(stem, folder, header_row):
    path = os.path.join(folder, f"{stem}.xlsx")
    df = pd.read_excel(path, header=header_row)
    return df


def clean_table(stem, df):
    """Apply normalize_ticker to company_id and normalize_year to year cols.
    Returns (clean_df, rejected_count)."""
    before = len(df)

    if COMPANY_ID_COL in df.columns:
        df[COMPANY_ID_COL] = df[COMPANY_ID_COL].apply(normalize_ticker)
        df = df[df[COMPANY_ID_COL].notna()]
    elif stem == "companies" and "id" in df.columns:
        df = df.rename(columns={"id": "company_id"})
        df["company_id"] = df["company_id"].apply(normalize_ticker)
        df = df[df["company_id"].notna()]

    # Column-name mismatches found by inspecting the raw files vs. schema.sql
    if stem == "documents" and "Annual_Report" in df.columns:
        df = df.rename(columns={"Annual_Report": "annual_report"})

    if stem in YEAR_TABLES:
        year_col = YEAR_TABLES[stem]
        df[year_col] = df[year_col].apply(normalize_year)
        if year_col != "year":
            df = df.rename(columns={year_col: "year"})
        # TTM rows are kept but flagged out of composite-key financial tables
        # that require a comparable fiscal year; drop only true unparsable ones
        df = df[df["year"].notna()]

    # DQ-01 / DQ-02: quarantine exact-duplicate primary-key rows instead of
    # letting the DB insert fail. Keep the first occurrence, log the rest.
    if stem in PK_COLUMNS:
        key = PK_COLUMNS[stem]
        dupe_mask = df.duplicated(subset=key, keep="first")
        if dupe_mask.any():
            dupes = df[dupe_mask]
            for _, row in dupes.iterrows():
                dupe_report_rows.append({
                    "table": stem,
                    "key": ", ".join(f"{k}={row[k]}" for k in key),
                    "source_id": row.get("id"),
                    "reason": "duplicate primary key - kept first occurrence, rejected this row",
                })
            df = df[~dupe_mask]

    rejected = before - len(df)
    return df, rejected


def write_table(conn, stem, df):
    """Insert a cleaned dataframe into its matching SQLite table,
    respecting the schema's actual column set."""
    cur = conn.cursor()
    cols_in_schema = [r[1] for r in cur.execute(f"PRAGMA table_info({stem})").fetchall()]
    cols_to_write = [c for c in df.columns if c in cols_in_schema]
    df_to_write = df[cols_to_write].copy()

    # bool -> int for sqlite (peer_groups.is_benchmark)
    for c in df_to_write.columns:
        if df_to_write[c].dtype == bool:
            df_to_write[c] = df_to_write[c].astype(int)

    df_to_write.to_sql(stem, conn, if_exists="append", index=False)


def main():
    os.makedirs("db", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.execute("PRAGMA foreign_keys = ON;")

    all_files = CORE_FILES + SUPP_FILES

    # companies must load first (parent table / FK target)
    all_files.sort(key=lambda x: 0 if x[0] == "companies" else 1)

    for stem, folder, header_row in all_files:
        try:
            raw_df = load_dataframe(stem, folder, header_row)
            source_rows = len(raw_df)
            clean_df, rejected = clean_table(stem, raw_df)

            # FK guard: drop rows whose company_id isn't a known company
            # (skip for the companies table itself)
            if stem != "companies":
                known = pd.read_sql("SELECT company_id FROM companies", conn)["company_id"].tolist()
                before_fk = len(clean_df)
                orphans = clean_df[~clean_df["company_id"].isin(known)]
                if len(orphans) > 0:
                    for cid in sorted(orphans["company_id"].unique()):
                        fk_orphan_rows.append({
                            "table": stem,
                            "company_id": cid,
                            "row_count": int((orphans["company_id"] == cid).sum()),
                            "reason": "company_id not present in companies.xlsx (92 companies) - "
                                      "this ticker has transaction data but no company master record",
                        })
                clean_df = clean_df[clean_df["company_id"].isin(known)]
                rejected += before_fk - len(clean_df)

            write_table(conn, stem, clean_df)
            conn.commit()
            log_audit(stem, source_rows, len(clean_df), rejected, "OK")
            print(f"[OK] {stem:20s} source={source_rows:5d}  loaded={len(clean_df):5d}  rejected={rejected}")
        except Exception as e:
            log_audit(stem, 0, 0, 0, "FAILED", str(e))
            print(f"[FAILED] {stem}: {e}")

    # FK check
    fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    print(f"\nPRAGMA foreign_key_check -> {len(fk_violations)} violations")

    conn.close()

    pd.DataFrame(audit_rows).to_csv(AUDIT_PATH, index=False)
    print(f"\nWrote {AUDIT_PATH}")
    print(f"Wrote {DB_PATH}")

    if dupe_report_rows:
        dupe_path = "output/duplicate_pk_rows.csv"
        pd.DataFrame(dupe_report_rows).to_csv(dupe_path, index=False)
        print(f"Wrote {dupe_path} ({len(dupe_report_rows)} quarantined rows - needs Day 6 manual review)")

    if fk_orphan_rows:
        fk_path = "output/fk_orphan_companies.csv"
        pd.DataFrame(fk_orphan_rows).drop_duplicates().to_csv(fk_path, index=False)
        n_companies = pd.DataFrame(fk_orphan_rows)["company_id"].nunique()
        print(f"Wrote {fk_path} ({n_companies} tickers referenced in transaction data "
              f"but missing from companies.xlsx - needs Day 6 manual review / companies.xlsx fix)")


if __name__ == "__main__":
    main()
