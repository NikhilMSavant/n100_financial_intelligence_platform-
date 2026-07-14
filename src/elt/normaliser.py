import re


def normalize_year(year):

    """
    Convert all year values into integers.

    Examples:
        2023.0 -> 2023
        "FY2022" -> 2022
        "2024" -> 2024
    """

    if year is None:
        return None

    year = str(year).strip()

    match = re.search(r"\d{4}", year)

    if match:
        return int(match.group())

    return None


def normalize_ticker(ticker):

    """
    Standardize stock tickers.

    Examples:
        "tcs" -> "TCS"
        "INFY.NS" -> "INFY"
        "SBIN.BO" -> "SBIN"
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(".BO", "")

    return ticker