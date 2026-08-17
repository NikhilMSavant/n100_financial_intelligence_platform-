import sqlite3
from fastapi import APIRouter, HTTPException
from ..deps import DB_PATH

router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{ticker}")
def market_cap_history(ticker: str, from_year: int = None, to_year: int = None):
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) 2019-2024."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ticker = ticker.upper()
    if not conn.execute("SELECT 1 FROM companies WHERE id=?", (ticker,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Ticker not found")
    q = "SELECT year, market_cap_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap WHERE company_id=?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"; params.append(from_year)
    if to_year:
        q += " AND year <= ?"; params.append(to_year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows
