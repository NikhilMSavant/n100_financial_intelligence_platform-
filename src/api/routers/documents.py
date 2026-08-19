import sqlite3
from fastapi import APIRouter, HTTPException
from ..deps import DB_PATH

router = APIRouter(tags=["documents"])


@router.get("/companies/{ticker}/documents")
def company_documents(ticker: str, from_year: int = None, to_year: int = None):
    """Annual report links with is_url_valid boolean flag for each."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ticker = ticker.upper()
    if not conn.execute("SELECT 1 FROM companies WHERE id=?", (ticker,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Ticker not found")
    q = "SELECT year, annual_report FROM documents WHERE company_id=?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"; params.append(from_year)
    if to_year:
        q += " AND year <= ?"; params.append(to_year)
    q += " ORDER BY year DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [{"year": r["year"], "annual_report": r["annual_report"],
             "is_url_valid": isinstance(r["annual_report"], str) and r["annual_report"].startswith("http")}
            for r in rows]
