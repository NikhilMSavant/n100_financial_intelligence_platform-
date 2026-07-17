"""
normaliser.py
-------------
Day 2 deliverable: normalize_year() and normalize_ticker().

Built from actual patterns found in the 12 source files:
  - "Dec 2012", "Mar 2014"        -> clean "Mon YYYY"
  - "Mar-13", "Mar-24"            -> hyphenated 2-digit year (cashflow.xlsx)
  - "TTM"                         -> trailing-twelve-months sentinel (profitandloss.xlsx)
  - "Mar 2023 15", "Mar 2016 9m"  -> corrupted rows with trailing junk (profitandloss.xlsx)
  - "2013", "2024.5"              -> bare / malformed year, no month (balancesheet.xlsx)
  - 2024 (int)                    -> documents.xlsx 'Year' column, already clean
"""

import re

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

TTM_SENTINEL = "TTM"


class YearNormalizationError(ValueError):
    """Raised when a year value cannot be confidently normalized."""


def normalize_year(raw_value, *, default_month=3, strict=False):
    """
    Normalize a messy 'year' field into a canonical 'YYYY-MM' string.

    Indian fiscal years default to a March year-end, so a bare year like
    "2013" (no month) is assumed to mean FY ending March 2013 -> "2013-03".
    This is a business assumption, not a guess: it's documented here and in
    the DQ rules doc, so it can be revisited if wrong.

    Special case: "TTM" (trailing twelve months) is not a fiscal year end at
    all -- it's returned as the literal string "TTM" so callers can decide
    whether to exclude it from year-indexed joins/PKs.

    Parameters
    ----------
    raw_value : str | int | float | None
    default_month : int, the month to assume when only a year is given
    strict : if True, raise YearNormalizationError on anything unparseable
             instead of returning None

    Returns
    -------
    str | None : "YYYY-MM", "TTM", or None if unparseable and strict=False
    """
    if raw_value is None:
        return None

    # int/float years (e.g. documents.xlsx 'Year' = 2024, or a stray 2024.5)
    if isinstance(raw_value, (int, float)):
        year_int = int(round(raw_value))
        if 1990 <= year_int <= 2100:
            return f"{year_int}-{default_month:02d}"
        if strict:
            raise YearNormalizationError(f"Numeric year out of range: {raw_value!r}")
        return None

    text = str(raw_value).strip()
    if not text:
        return None

    if text.upper() == TTM_SENTINEL:
        return TTM_SENTINEL

    # Strip known trailing junk like " 15" or " 9m" seen in profitandloss.xlsx
    # (keep the "Mon YYYY" / "Mon-YY" head, discard anything after it)
    cleaned = text

    # Try "Mon YYYY" or "Mon-YY" or "Mon-YYYY" (with arbitrary trailing junk)
    m = re.match(
        r"^\s*([A-Za-z]{3})[\s\-]?(\d{2,4})",
        cleaned,
    )
    if m:
        mon_str, year_str = m.group(1).lower(), m.group(2)
        month = MONTHS.get(mon_str)
        if month is not None:
            year_int = int(year_str)
            if year_int < 100:  # 2-digit year e.g. "13" -> 2013
                year_int += 2000
            if 1990 <= year_int <= 2100:
                return f"{year_int}-{month:02d}"

    # Bare numeric year, possibly with a stray decimal (e.g. "2024.5")
    m = re.match(r"^\s*(\d{4})(?:\.\d+)?\s*$", cleaned)
    if m:
        year_int = int(m.group(1))
        if 1990 <= year_int <= 2100:
            return f"{year_int}-{default_month:02d}"

    if strict:
        raise YearNormalizationError(f"Unparseable year value: {raw_value!r}")
    return None


def normalize_ticker(raw_value, *, strict=False):
    """
    Normalize a company_id / ticker value: strip whitespace, uppercase,
    collapse internal whitespace. Source files were found to already be
    clean (no case/whitespace issues detected on inspection), but the
    loader must not assume that stays true for future refreshes.

    Returns
    -------
    str | None
    """
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text:
        if strict:
            raise ValueError("Empty ticker value")
        return None

    text = re.sub(r"\s+", "", text)  # tickers never contain internal spaces
    return text.upper()


if __name__ == "__main__":
    # quick manual smoke test
    samples_year = ["Dec 2012", "Mar-13", "TTM", "Mar 2023 15", "Mar 2016 9m",
                     "2013", 2024, 2024.5, None, "garbage"]
    for s in samples_year:
        print(f"{s!r:20} -> {normalize_year(s)!r}")

    samples_ticker = [" abb ", "TCS", "hdfcbank", None, "  "]
    for s in samples_ticker:
        print(f"{s!r:20} -> {normalize_ticker(s)!r}")
