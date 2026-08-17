import sys, pathlib, sqlite3
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
DB = str(pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "nifty100.db")


def _conn():
    return sqlite3.connect(DB)


def test_companies_count():
    conn = _conn()
    n = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    conn.close()
    assert n == 92, f"expected 92 companies, got {n}"

def test_companies_columns():
    conn = _conn()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(companies)").fetchall()]
    conn.close()
    for c in ["id", "company_name", "roce_percentage", "roe_percentage"]:
        assert c in cols

def test_pl_columns():
    conn = _conn()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(profitandloss)").fetchall()]
    conn.close()
    for c in ["sales", "net_profit", "eps", "operating_profit"]:
        assert c in cols

def test_bs_columns():
    conn = _conn()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(balancesheet)").fetchall()]
    conn.close()
    for c in ["equity_capital", "reserves", "borrowings", "total_assets"]:
        assert c in cols

def test_cf_columns():
    conn = _conn()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cashflow)").fetchall()]
    conn.close()
    for c in ["operating_activity", "investing_activity", "financing_activity"]:
        assert c in cols

def test_fk_integrity_zero():
    conn = _conn()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    assert len(violations) == 0

def test_no_duplicate_pl_keys():
    conn = _conn()
    n_total = conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0]
    n_distinct = conn.execute("SELECT COUNT(*) FROM (SELECT DISTINCT company_id, year FROM profitandloss)").fetchone()[0]
    conn.close()
    assert n_total == n_distinct

def test_sectors_row_count():
    conn = _conn()
    n = conn.execute("SELECT COUNT(*) FROM sectors").fetchone()[0]
    conn.close()
    assert n == 92

def test_market_cap_year_range():
    conn = _conn()
    rows = conn.execute("SELECT MIN(year), MAX(year) FROM market_cap").fetchall()
    conn.close()
    lo, hi = rows[0]
    assert lo >= 2019 and hi <= 2024

def test_stock_prices_nonempty():
    conn = _conn()
    n = conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0]
    conn.close()
    assert n > 1000
