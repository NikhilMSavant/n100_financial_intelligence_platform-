"""Normalisation utilities for tickers and financial-year labels."""
import re

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "march": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08", "sep": "09",
    "sept": "09", "oct": "10", "nov": "11", "dec": "12", "december": "12",
}

YEAR_RE = re.compile(r"^\d{4}-\d{2}$")


def normalize_ticker(raw) -> str:
    """Strip whitespace and upper-case a company ticker; raise if out of range."""
    if raw is None:
        raise ValueError("MISSING_TICKER")
    t = str(raw).strip().upper()
    if not (2 <= len(t) <= 12):
        raise ValueError(f"TICKER_LENGTH_OUT_OF_RANGE:{t}")
    return t


def normalize_year(raw) -> str:
    """Convert a variety of raw financial-year labels to 'YYYY-MM'.

    Supported inputs: 'Mar-23', 'Mar 23', 'Mar 2023', 'March-2023', '2023',
    'FY23', 'Dec-22', 'Dec 2012', already-normalised 'YYYY-MM'.
    Unparseable input returns 'PARSE_ERROR'.
    """
    if raw is None:
        return "PARSE_ERROR"
    s = str(raw).strip()
    if not s:
        return "PARSE_ERROR"

    if YEAR_RE.match(s):
        return s

    if s.upper() == "TTM":
        return "PARSE_ERROR"  # trailing-twelve-months has no fixed FY end; excluded from time series

    # Pure 4-digit year -> assume March FY close
    if re.match(r"^\d{4}$", s):
        return f"{s}-03"

    # FY23 / FY2023
    m = re.match(r"^FY\s*(\d{2,4})$", s, re.IGNORECASE)
    if m:
        yy = m.group(1)
        year = f"20{yy}" if len(yy) == 2 else yy
        return f"{year}-03"

    # Month-Year or Month Year variants: Mar-23, Mar 23, Mar-2023, Mar 2023, March-2023
    m = re.match(r"^([A-Za-z]+)[\s\-]?(\d{2,4})$", s)
    if m:
        mon_raw, yr_raw = m.group(1).lower(), m.group(2)
        mon = MONTHS.get(mon_raw)
        if mon is None:
            return "PARSE_ERROR"
        year = f"20{yr_raw}" if len(yr_raw) == 2 else yr_raw
        return f"{year}-{mon}"

    return "PARSE_ERROR"
