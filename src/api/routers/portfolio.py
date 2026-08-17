import pathlib
import pandas as pd
from fastapi import APIRouter

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/stats")
def portfolio_stats():
    """P10-P90 percentile table for 10 core KPIs across all 92 companies."""
    path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output" / "portfolio_stats.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    return df.to_dict(orient="records")
