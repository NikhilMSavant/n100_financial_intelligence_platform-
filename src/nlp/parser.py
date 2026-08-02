"""
parser.py
---------
Day 29 deliverable: parses the free-text metric fields in the `analysis`
table (loaded from data/raw/analysis.xlsx by src/etl/loader.py) into
structured (period_years, value_pct) pairs using the spec's regex, then
cross-validates the parsed CAGR values against the Ratio Engine's own
computed CAGR (src/analytics/cagr.py) for the two fields where a like-for-
like computed benchmark exists.

Known, documented data limitation: the `analysis` table only has rows for
4 of the 92 companies (HDFCBANK, INFY, SBILIFE, TCS) - the raw source file
data/raw/analysis.xlsx itself only ever contained analysis text for 5
tickers (the 5th, WIPRO, is correctly excluded at load time as an FK
orphan - it has no row in companies.xlsx's 92-company master list, see
output/fk_orphan_companies.csv). This is not a bug in this parser; it
means analysis_parsed.csv and the cross-validation output will only ever
cover those 4 companies until analysis.xlsx itself is extended with more
source data.

Regex, exactly as specified:
    (\\d+)\\s*Years?:?\\s*([\\d.]+)%
Known, deliberate limitation of using this exact pattern: it has no
negative-sign handling, so an entry like "1 Year: -2%" will NOT match and
will be logged to parse_failures.csv rather than silently mis-parsed as
2%. "TTM:" and "1 Year:"/"Last Year:" entries also don't match "N Years:"
by design and are logged as failures too - the spec's target fields are
specifically the *_Years-labeled entries (10/5/3 year windows).

Run with: python src/nlp/parser.py
(Run AFTER loader.py and populate_ratios.py, since it reads from
db/nifty100.db and cross-validates against financial_ratios / profitandloss.)
"""
import csv
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analytics"))
from cagr import compute_cagr_from_series

DB_PATH = "db/nifty100.db"
PARSED_PATH = "output/analysis_parsed.csv"
FAILURES_PATH = "output/parse_failures.csv"
CROSS_VALIDATION_PATH = "output/cagr_cross_validation.csv"

# Spec-given regex, used exactly as specified (see docstring above for its
# known negative-value limitation).
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%")

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]

# Only these two fields have a like-for-like computed CAGR to cross-validate
# against (the Ratio Engine computes revenue and PAT CAGR, not a stock-price
# CAGR or an ROE CAGR - ROE is a level/ratio, not a growth rate, so an
# "ROE CAGR" isn't a meaningful comparison and is intentionally excluded).
# Maps metric_type -> the profitandloss column to build a year series from.
CROSS_VALIDATABLE_FIELDS = {
    "compounded_sales_growth": "sales",
    "compounded_profit_growth": "net_profit",
}

# Cross-validate only 3yr and 5yr windows against a fresh independent
# computation from profitandloss - a 10yr window is included too since we
# have 12 fiscal years of history (2013-03 to 2024-03) for all 4 companies
# with analysis data, giving a genuine 10yr-apart start/end pair.
DIVERGENCE_THRESHOLD_PCT = 5.0


def fetch_analysis_rows(conn):
    rows = conn.execute(
        "SELECT company_id, compounded_sales_growth, compounded_profit_growth, "
        "stock_price_cagr, roe FROM analysis ORDER BY company_id, id"
    ).fetchall()
    return [
        {
            "company_id": r[0],
            "compounded_sales_growth": r[1],
            "compounded_profit_growth": r[2],
            "stock_price_cagr": r[3],
            "roe": r[4],
        }
        for r in rows
    ]


def parse_metric_text(text):
    """
    Applies PATTERN to a single text field.
    Returns (period_years: int, value_pct: float) on match, else None.
    """
    if text is None:
        return None
    match = PATTERN.search(str(text))
    if not match:
        return None
    period_years = int(match.group(1))
    value_pct = float(match.group(2))
    return period_years, value_pct


def parse_all(conn):
    """
    Returns (parsed_rows, failure_rows) - lists of dicts ready to write
    straight to CSV.
    """
    parsed_rows = []
    failure_rows = []

    for row in fetch_analysis_rows(conn):
        company_id = row["company_id"]
        for metric_type in TARGET_FIELDS:
            raw_text = row[metric_type]
            result = parse_metric_text(raw_text)
            if result is None:
                failure_rows.append({
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "raw_text": raw_text,
                })
            else:
                period_years, value_pct = result
                parsed_rows.append({
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period_years,
                    "value_pct": value_pct,
                })

    return parsed_rows, failure_rows


def fetch_year_series(conn, company_id, column):
    """
    Returns {year: value} for a company from profitandloss, EXCLUDING the
    'TTM' pseudo-year - a trailing-N-year CAGR should be measured between
    complete fiscal years, and mixing in a partial TTM year would distort
    the window (e.g. a "10 year" CAGR should end at FY2024, not at a
    part-year TTM figure).
    """
    rows = conn.execute(
        f"SELECT year, {column} FROM profitandloss WHERE company_id = ? AND year != 'TTM'",
        (company_id,),
    ).fetchall()
    return {year: value for year, value in rows if value is not None}


def cross_validate(conn, parsed_rows):
    """
    For each parsed row on a cross-validatable field, independently
    recomputes the same-period CAGR from profitandloss using the Ratio
    Engine's own compute_cagr_from_series(), and flags any row where the
    two values diverge by more than DIVERGENCE_THRESHOLD_PCT (percentage
    points - both sides are already percentages, so a plain difference is
    the natural way to express "how far apart are these two numbers").

    Returns a list of dicts covering every cross-validatable row (not just
    the flagged ones) so the output is auditable, with a `flagged` column
    marking which ones exceed the threshold.
    """
    results = []
    series_cache = {}  # (company_id, column) -> {year: value}, avoid re-querying

    for row in parsed_rows:
        metric_type = row["metric_type"]
        if metric_type not in CROSS_VALIDATABLE_FIELDS:
            continue

        company_id = row["company_id"]
        period_years = row["period_years"]
        parsed_value = row["value_pct"]
        column = CROSS_VALIDATABLE_FIELDS[metric_type]

        cache_key = (company_id, column)
        if cache_key not in series_cache:
            series_cache[cache_key] = fetch_year_series(conn, company_id, column)
        series = series_cache[cache_key]

        computed = compute_cagr_from_series(series, period_years)
        computed_value = computed["value"]
        computed_flag = computed["flag"]

        if computed_value is None:
            divergence = None
            flagged = False
        else:
            divergence = round(abs(parsed_value - computed_value), 2)
            flagged = divergence > DIVERGENCE_THRESHOLD_PCT

        results.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "period_years": period_years,
            "parsed_value_pct": parsed_value,
            "computed_value_pct": round(computed_value, 2) if computed_value is not None else None,
            "computed_flag": computed_flag or "",
            "divergence_pct": divergence,
            "flagged_for_review": flagged,
        })

    return results


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    conn = sqlite3.connect(DB_PATH)

    parsed_rows, failure_rows = parse_all(conn)
    write_csv(PARSED_PATH, parsed_rows, ["company_id", "metric_type", "period_years", "value_pct"])
    write_csv(FAILURES_PATH, failure_rows, ["company_id", "metric_type", "raw_text"])

    cross_val_rows = cross_validate(conn, parsed_rows)
    write_csv(
        CROSS_VALIDATION_PATH,
        cross_val_rows,
        ["company_id", "metric_type", "period_years", "parsed_value_pct",
         "computed_value_pct", "computed_flag", "divergence_pct", "flagged_for_review"],
    )

    conn.close()

    n_companies = len({r["company_id"] for r in parsed_rows} | {r["company_id"] for r in failure_rows})
    n_flagged = sum(1 for r in cross_val_rows if r["flagged_for_review"])

    print(f"Parsed {len(parsed_rows)} entries successfully across {n_companies} companies.")
    print(f"Logged {len(failure_rows)} entries that did not match the pattern -> {FAILURES_PATH}")
    print(f"Cross-validated {len(cross_val_rows)} entries -> {CROSS_VALIDATION_PATH}")
    print(f"  {n_flagged} flagged for manual review (divergence > {DIVERGENCE_THRESHOLD_PCT}%)")
    print(
        f"NOTE: analysis table only covers {n_companies} of 92 companies - "
        "see module docstring for why."
    )


if __name__ == "__main__":
    main()
