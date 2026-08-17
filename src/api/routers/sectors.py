import sqlite3
import pathlib
from fastapi import APIRouter, HTTPException
from ..deps import DB_PATH

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def list_sectors():
    """All sectors with company_count, median_roe, median_pe, median_de."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from screener.engine import load_latest_universe
    conn = sqlite3.connect(DB_PATH)
    df = load_latest_universe(conn)
    conn.close()
    grp = df.groupby("broad_sector").agg(
        company_count=("company_id", "count"),
        median_roe=("return_on_equity_pct", "median"),
        median_pe=("pe_ratio", "median"),
        median_de=("debt_to_equity", "median"),
    ).reset_index()
    return grp.where(grp.notna(), None).to_dict(orient="records")


@router.get("/sectors/{sector}/companies")
def sector_companies(sector: str, year: str = None):
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from screener.engine import load_latest_universe
    conn = sqlite3.connect(DB_PATH)
    df = load_latest_universe(conn)
    conn.close()
    result = df[df["broad_sector"] == sector]
    if result.empty:
        raise HTTPException(status_code=404, detail=f"Unknown sector '{sector}'")
    cols = ["company_id", "company_name", "return_on_equity_pct", "return_on_capital_employed_pct",
            "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "pat_cagr_5yr",
            "pe_ratio", "composite_quality_score"]
    return result[cols].where(result[cols].notna(), None).to_dict(orient="records")
