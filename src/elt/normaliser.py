import re

def normalize_year(year):

    if year is None:
        return None

    year = str(year).strip()

    if year.upper() == "TTM":
        return "TTM"

    if year.startswith("Mar"):
        return year

    return year


def normalize_ticker(ticker):

    ticker = str(ticker).strip().upper()

    mapping = {

        "ULTRATECH": "ULTRACEMCO",
        "VEDANTA": "VEDL",
        "VARUNBEV": "VBL",
        "UNITEDSPIRITS": "UNITDSPR",
        "UNIONBK": "UNIONBANK",
        "CADILAHC": "ZYDUSLIFE"

    }

    return mapping.get(
        ticker,
        ticker
    )