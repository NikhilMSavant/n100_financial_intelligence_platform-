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

# Known source-data errors in companies.xlsx, corrected post-load so they
# don't need re-discovering every time the pipeline runs.
#
# The "ABB" record's history: Sprint 4 Day 27 first found companies.xlsx
# had Abbott India's name/description under ticker "ABB" and corrected
# just that. A later full re-verification (prompted by the person testing
# the live dashboard and noticing the Annual Reports screen's BSE links
# for "ABB" all pointed at BSE scrip 500488) found the mismatch goes much
# deeper: 500488 is Abbott India's real BSE scrip code (ABB India's real
# code is 500002, a different company entirely - confirmed via BSE's own
# published scrip-code listings). Cross-checking confirmed the ENTIRE
# profitandloss/balancesheet/cashflow history under company_id "ABB" is
# Abbott India's real financials, not ABB India's: this dataset's FY2024
# sales of Rs 5,849 Cr for "ABB" matches Abbott India's own published
# FY2024 sales of Rs 5,849 Cr exactly (a pharmaceutical company's margins
# and scale, not an industrial automation company's).
#
# Decision (person's explicit choice, given 3 options): treat this
# company_id's data as what it actually is - Abbott India's - rather than
# trying to backfill genuine ABB India financials we don't have and can't
# source from these raw files. company_id itself is left as "ABB" (not
# renamed to e.g. "ABBOTINDIA") since nothing in this codebase treats
# company_id as a display value and renaming a primary key used as an FK
# by 13 other tables is a much larger, separate change than what was
# asked for; company_name now makes the true identity visible everywhere
# it's displayed. nse_profile/bse_profile were already correctly pointing
# at ABBOTINDIA/500488 and are left as-is.
#
# Net effect: ABB India Ltd (the real industrials/automation company) is
# NOT present anywhere in this 92-company dataset under any company_id -
# there is no source data for it at all, only for Abbott India under a
# ticker that used to display the wrong name.
COMPANY_NAME_CORRECTIONS = {
    "ABB": {
        "company_name": "Abbott India Ltd",
        "about_company": (
            "Abbott India Ltd is a subsidiary of the US-based multinational "
            "Abbott Laboratories, and has operated in India since 1944. The "
            "company develops and markets branded generic pharmaceuticals, "
            "diagnostics, and nutrition products, distributing primarily "
            "through independent pharmaceutical distributors across India."
        ),
    },
}

# Sector correction paired with the COMPANY_NAME_CORRECTIONS entry above -
# sectors.xlsx had classified this company_id as Industrials/Capital Goods
# (correct for the real ABB India, wrong for the Abbott India data actually
# stored under it). Applied once the sectors table is loaded - see the
# `if stem == "sectors"` hook below.
SECTOR_CORRECTIONS = {
    "ABB": {"broad_sector": "Healthcare", "sub_sector": "Pharmaceuticals"},
}

# Known bad rows found via validator.py's CRITICAL findings (post-Sprint-4
# full re-verification of Sprint 1's "CRITICAL failures resolved" exit
# criterion, which had never actually been enforced - validator.py only
# ever reported findings, nothing consumed them). Each entry is a single
# company-year with every financial field zeroed out (e.g. sales=0 AND
# total_assets=0 AND total_liabilities=0 simultaneously) - not a real
# business event a listed company would report, so this is placeholder/
# corrupted source data rather than a legitimate (if unusual) year.
# Quarantined here, in the same spot and style as the PK-duplicate and
# FK-orphan rejections below, rather than left silently loaded.
#
# NOT included here: JIOFIN's DQ-16 CRITICAL (only 2 fiscal years of P&L
# history, Jio Financial Services demerged/listed in 2023). Its 2 rows
# are genuine, non-corrupted data - the "failure" is a real data-coverage
# limitation for a recently-listed company, not a bad row to drop. Every
# CAGR/growth computation downstream already handles this correctly via
# cagr.py's INSUFFICIENT flag rather than crashing or silently omitting
# it. Documented as an accepted exception, not "fixed" by deleting valid
# data - see output/dq_critical_resolution_log.md.
KNOWN_BAD_ROWS = {
    "profitandloss": [("ADANIENSOL", "2014-03")],
    "balancesheet": [("ADANIENSOL", "2014-03")],
}
quarantined_bad_rows = []


def apply_known_data_corrections(conn):
    """Applies COMPANY_NAME_CORRECTIONS after the companies table is
    loaded, so known source-data errors don't silently reappear on every
    pipeline re-run."""
    for company_id, corrections in COMPANY_NAME_CORRECTIONS.items():
        set_clause = ", ".join(f"{col} = ?" for col in corrections)
        values = list(corrections.values()) + [company_id]
        conn.execute(f"UPDATE companies SET {set_clause} WHERE company_id = ?", values)
    conn.commit()


def apply_sector_corrections(conn):
    """Applies SECTOR_CORRECTIONS after the sectors table is loaded -
    same idea as apply_known_data_corrections, separate function because
    it targets a different table that loads later in the pipeline."""
    for company_id, corrections in SECTOR_CORRECTIONS.items():
        set_clause = ", ".join(f"{col} = ?" for col in corrections)
        values = list(corrections.values()) + [company_id]
        conn.execute(f"UPDATE sectors SET {set_clause} WHERE company_id = ?", values)
    conn.commit()

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

    # Quarantine known-bad rows (see KNOWN_BAD_ROWS docstring above) before
    # PK dedup, so they're rejected and counted the same way duplicates are.
    if stem in KNOWN_BAD_ROWS:
        bad_keys = set(KNOWN_BAD_ROWS[stem])
        bad_mask = df.apply(lambda r: (r["company_id"], r["year"]) in bad_keys, axis=1)
        if bad_mask.any():
            for _, row in df[bad_mask].iterrows():
                quarantined_bad_rows.append({
                    "table": stem,
                    "company_id": row["company_id"],
                    "year": row["year"],
                    "reason": "all financial fields zeroed out - not a real business event, "
                              "flagged CRITICAL by validator.py DQ-06/DQ-10",
                })
            df = df[~bad_mask]

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

            if stem == "companies":
                apply_known_data_corrections(conn)
            if stem == "sectors":
                apply_sector_corrections(conn)

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

    if quarantined_bad_rows:
        bad_path = "output/quarantined_critical_rows.csv"
        pd.DataFrame(quarantined_bad_rows).to_csv(bad_path, index=False)
        print(f"Wrote {bad_path} ({len(quarantined_bad_rows)} CRITICAL rows quarantined)")

    with open("output/dq_critical_resolution_log.md", "w") as f:
        f.write(
            "# DQ CRITICAL Failure Resolution Log\n\n"
            "Every CRITICAL finding from validator.py's Day 3 rules (DQ-01..DQ-16), "
            "as required by Sprint 1's exit criterion (\"CRITICAL failures resolved\"). "
            "Written by loader.py on every run, alongside output/quarantined_critical_rows.csv.\n\n"
            "## Resolved by quarantining the row\n\n"
            "- **ADANIENSOL, 2014-03** (profitandloss + balancesheet): every financial "
            "field zeroed out simultaneously (sales=0, total_assets=0, "
            "total_liabilities=0) - not a real business event, corrupted/placeholder "
            "source data. Rejected at load time via KNOWN_BAD_ROWS in loader.py. "
            "Triggered DQ-06 and DQ-10.\n\n"
            "## Accepted as a genuine data-coverage limitation (not quarantined)\n\n"
            "- **JIOFIN**: only 2 distinct fiscal years of P&L data (2023-03, 2024-03), "
            "below DQ-16's 3-year CRITICAL threshold. Jio Financial Services was "
            "demerged from Reliance Industries and listed in 2023, so this is genuine, "
            "uncorrupted data for a recently-listed company - there is no earlier "
            "history to load. Rejecting these 2 valid rows would remove real data "
            "for no benefit. Every downstream CAGR/growth computation already handles "
            "this correctly via cagr.py's INSUFFICIENT flag (returns None + a named "
            "flag rather than crashing or producing a misleading number from too "
            "short a window) - verified in tests/kpi/test_cagr.py.\n"
        )
    print("Wrote output/dq_critical_resolution_log.md")


if __name__ == "__main__":
    main()
