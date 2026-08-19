"""Shared SQLite connection dependency + app-wide constants for the API layer."""
import sqlite3
import pathlib
import time

DB_PATH = str(pathlib.Path(__file__).resolve().parent.parent / "data" / "nifty100.db")
APP_START_TIME = time.time()
VERSION = "1.0.0"

TABLES = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis", "documents",
          "prosandcons", "sectors", "market_cap", "stock_prices", "peer_groups", "financial_ratios"]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def db_row_counts():
    conn = sqlite3.connect(DB_PATH)
    counts = {}
    for t in TABLES:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = None
    conn.close()
    return counts
