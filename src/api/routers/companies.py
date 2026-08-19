import sqlite3
from fastapi import APIRouter, HTTPException, Query, Response
from ..deps import DB_PATH

router = APIRouter(tags=["companies"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _company_exists(conn, ticker):
    return conn.execute("SELECT 1 FROM companies WHERE id=?", (ticker.upper(),)).fetchone() is not None


@router.get("/companies")
def list_companies(sector: str = None, market_cap_category: str = None, search: str = None):
    """List all 92 companies. Optional filters: sector, market_cap_category, search (partial name/ticker)."""
    conn = _conn()
    q = """SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, c.roe_percentage AS roe_pct,
                  c.roce_percentage AS roce_pct
           FROM companies c LEFT JOIN sectors s ON c.id = s.company_id WHERE 1=1"""
    params = []
    if sector:
        q += " AND s.broad_sector = ?"; params.append(sector)
    if market_cap_category:
        q += " AND s.market_cap_category = ?"; params.append(market_cap_category)
    if search:
        q += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params += [f"%{search.upper()}%", f"%{search}%"]
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/companies/{ticker}")
def company_profile(ticker: str):
    """Full company profile: companies fields + latest year KPIs + sector data."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    company = dict(conn.execute("SELECT * FROM companies WHERE id=?", (ticker,)).fetchone())
    sector = conn.execute("SELECT * FROM sectors WHERE company_id=?", (ticker,)).fetchone()
    latest_ratio = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id=? AND net_profit_margin_pct IS NOT NULL "
        "ORDER BY year DESC LIMIT 1", (ticker,)).fetchone()
    conn.close()
    return {**company, "sector": dict(sector) if sector else None,
            "latest_kpis": dict(latest_ratio) if latest_ratio else None}


@router.get("/companies/{ticker}/pl")
def company_pl(ticker: str, from_year: str = None, to_year: str = None):
    """P&L history array. from_year/to_year in YYYY-MM."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close(); raise HTTPException(status_code=404, detail="Ticker not found")
    q = "SELECT * FROM profitandloss WHERE company_id=?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"; params.append(from_year)
    if to_year:
        q += " AND year <= ?"; params.append(to_year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/companies/{ticker}/bs")
def company_bs(ticker: str, from_year: str = None, to_year: str = None):
    """Balance sheet history array."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close(); raise HTTPException(status_code=404, detail="Ticker not found")
    q = "SELECT * FROM balancesheet WHERE company_id=?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"; params.append(from_year)
    if to_year:
        q += " AND year <= ?"; params.append(to_year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/companies/{ticker}/cashflow")
def company_cf(ticker: str, from_year: str = None, to_year: str = None):
    """Cash flow history array."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close(); raise HTTPException(status_code=404, detail="Ticker not found")
    q = "SELECT * FROM cashflow WHERE company_id=?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"; params.append(from_year)
    if to_year:
        q += " AND year <= ?"; params.append(to_year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/companies/{ticker}/ratios")
def company_ratios(ticker: str, year: str = None):
    """All computed KPIs per year. Optional single-year filter."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close(); raise HTTPException(status_code=404, detail="Ticker not found")
    if year:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id=? AND year=?", (ticker, year)).fetchall()]
    else:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year", (ticker,)).fetchall()]
    conn.close()
    return rows


@router.get("/companies/{ticker}/tearsheet")
def company_tearsheet(ticker: str):
    """Return the pre-generated tearsheet PDF as a binary download."""
    import pathlib
    ticker = ticker.upper()
    path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "reports" / "tearsheets" / f"{ticker}_tearsheet.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Tearsheet not found for this ticker")
    return Response(content=path.read_bytes(), media_type="application/pdf",
                     headers={"Content-Disposition": f"attachment; filename={ticker}_tearsheet.pdf"})


@router.get("/companies/{ticker}/peers/compare")
def peers_compare(ticker: str, year: str = None):
    """Radar data: 8 axis metrics for company + peer group average + benchmark company."""
    conn = _conn()
    ticker = ticker.upper()
    if not _company_exists(conn, ticker):
        conn.close(); raise HTTPException(status_code=404, detail="Ticker not found")
    group = conn.execute("SELECT peer_group_name, is_benchmark FROM peer_groups WHERE company_id=?", (ticker,)).fetchone()
    if not group:
        conn.close()
        return {"company_id": ticker, "message": "No peer group assigned"}
    group_name = group["peer_group_name"]
    members = [dict(r) for r in conn.execute(
        "SELECT company_id FROM peer_groups WHERE peer_group_name=?", (group_name,)).fetchall()]
    benchmark = conn.execute(
        "SELECT company_id FROM peer_groups WHERE peer_group_name=? AND is_benchmark=1", (group_name,)).fetchone()
    axes = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"]
    conn.close()
    return {"company_id": ticker, "peer_group": group_name, "axes": axes,
            "benchmark_company": benchmark["company_id"] if benchmark else None,
            "member_count": len(members)}
