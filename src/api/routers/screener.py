import sys
import pathlib
from fastapi import APIRouter, HTTPException
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

router = APIRouter(tags=["screener"])


@router.get("/screener")
def screener(min_roe: float = None, max_de: float = None, min_fcf: float = None, sector: str = None,
             min_rev_cagr_5yr: float = None, min_pat_cagr_5yr: float = None, max_pe: float = None):
    """Screener endpoint with query-param thresholds. Returns ranked company list."""
    import sqlite3
    from screener.engine import load_latest_universe
    for name, val in [("min_roe", min_roe), ("max_de", max_de), ("min_fcf", min_fcf),
                       ("min_rev_cagr_5yr", min_rev_cagr_5yr), ("min_pat_cagr_5yr", min_pat_cagr_5yr),
                       ("max_pe", max_pe)]:
        if val is not None and not isinstance(val, (int, float)):
            raise HTTPException(status_code=400, detail=f"Invalid value for {name}")

    conn = sqlite3.connect(str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"))
    df = load_latest_universe(conn)
    conn.close()

    if sector:
        df = df[df["broad_sector"] == sector]
    if min_roe is not None:
        df = df[df["return_on_equity_pct"] >= min_roe]
    if max_de is not None:
        df = df[(df["debt_to_equity"] <= max_de) | (df["broad_sector"] == "Financials")]
    if min_fcf is not None:
        df = df[df["free_cash_flow_cr"] >= min_fcf]
    if min_rev_cagr_5yr is not None:
        df = df[df["revenue_cagr_5yr"] >= min_rev_cagr_5yr]
    if min_pat_cagr_5yr is not None:
        df = df[df["pat_cagr_5yr"] >= min_pat_cagr_5yr]
    if max_pe is not None:
        df = df[df["pe_ratio"] <= max_pe]

    df = df.sort_values("composite_quality_score", ascending=False)
    cols = ["company_id", "company_name", "broad_sector", "composite_quality_score",
            "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr",
            "pat_cagr_5yr", "pe_ratio"]
    return df[cols].where(df[cols].notna(), None).to_dict(orient="records")
