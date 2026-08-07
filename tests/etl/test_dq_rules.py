import os, sqlite3, sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")



def conn():
    c = sqlite3.connect(DB_PATH)
    yield c
    c.close()


def test_companies_row_count(conn):
    assert conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 92


def test_foreign_key_check_clean(conn):
    conn.execute("PRAGMA foreign_keys = ON")
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_no_duplicate_company_year_pl(conn):
    df = pd.read_sql("SELECT company_id, year, COUNT(*) c FROM profitandloss GROUP BY 1,2 HAVING c>1", conn)
    assert len(df) == 0


def test_no_duplicate_company_year_bs(conn):
    df = pd.read_sql("SELECT company_id, year, COUNT(*) c FROM balancesheet GROUP BY 1,2 HAVING c>1", conn)
    assert len(df) == 0


def test_no_zero_sales_rows(conn):
    df = pd.read_sql("SELECT * FROM profitandloss WHERE sales <= 0", conn)
    assert len(df) == 0


def test_no_zero_total_assets_rows(conn):
    df = pd.read_sql("SELECT * FROM balancesheet WHERE total_assets <= 0", conn)
    assert len(df) == 0


def test_pl_row_count_reasonable(conn):
    n = conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0]
    assert 900 <= n <= 1276


def test_bs_row_count_reasonable(conn):
    n = conn.execute("SELECT COUNT(*) FROM balancesheet").fetchone()[0]
    assert 900 <= n <= 1312


def test_cf_row_count_reasonable(conn):
    n = conn.execute("SELECT COUNT(*) FROM cashflow").fetchone()[0]
    assert 900 <= n <= 1187


def test_stock_prices_loaded(conn):
    assert conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0] == 5520


def test_sectors_cover_all_companies(conn):
    n = conn.execute(
        "SELECT COUNT(*) FROM companies c LEFT JOIN sectors s ON c.company_id=s.company_id "
        "WHERE s.company_id IS NULL").fetchone()[0]
    assert n == 0


def test_validation_failures_file_has_no_critical(conn):
    path = os.path.join(ROOT, "output", "validation_failures.csv")
    df = pd.read_csv(path)
    assert (df.severity == "CRITICAL").sum() == 0


def test_peer_groups_loaded(conn):
    assert conn.execute("SELECT COUNT(*) FROM peer_groups").fetchone()[0] > 0


def test_market_cap_loaded_for_all_companies_latest_year(conn):
    n = conn.execute("SELECT COUNT(DISTINCT company_id) FROM market_cap").fetchone()[0]
    assert n >= 80
