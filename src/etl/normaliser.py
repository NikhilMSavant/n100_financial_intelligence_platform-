"""
normaliser.py — Sprint 1 / Day 02
Normalises raw year-labels and ticker strings coming out of the source
Excel workbooks into a consistent shape the rest of the pipeline can rely on.
"""
import re
import pandas as pd

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_YEAR_RE = re.compile(r"([A-Za-z]{3,})[\s\-]*'?(\d{2,4})")


def normalize_year(raw):
    """
    Turns labels like 'Mar 2014', 'Mar-13', 'Dec 2012', 'TTM' into a
    canonical fiscal year INT (the calendar year the statement is dated in),
    plus a 'is_ttm' flag folded into the return via None for TTM rows.

    Returns: int fiscal_year, or None if the row is a TTM / unparsable row.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "TTM":
        return None

    m = _YEAR_RE.match(s)
    if not m:
        return None
    _, year_part = m.groups()
    year = int(year_part)
    if year < 100:
        # 2-digit year e.g. 'Mar-13' -> 2013
        year += 2000
    return year


def normalize_month(raw):
    """Returns the 3-letter lowercase month abbreviation found in the label, or None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "TTM":
        return None
    m = _YEAR_RE.match(s)
    if not m:
        return None
    mon_part, _ = m.groups()
    mon_key = mon_part[:3].lower()
    return mon_key if mon_key in MONTH_MAP else None


def is_ttm(raw):
    return raw is not None and str(raw).strip().upper() == "TTM"


def normalize_ticker(raw):
    """
    Cleans a company_id / ticker string: strips whitespace, uppercases,
    removes stray punctuation that sometimes creeps in from Excel exports.
    """
    if raw is None:
        return None
    s = str(raw).strip().upper()
    s = re.sub(r"[^A-Z0-9\-&]", "", s)
    return s or None


def normalize_numeric(raw):
    """Best-effort coercion of a numeric-looking Excel cell to float, else None."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(",", "")
    if s in ("", "-", "NA", "N/A", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


if __name__ == "__main__":
    samples = ["Mar 2014", "Mar-13", "Dec 2012", "TTM", "Sep 2024", None, "  abc123  "]
    for s in samples:
        print(f"{s!r:15} -> year={normalize_year(s)} ttm={is_ttm(s)}")
