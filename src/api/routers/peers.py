import sqlite3
from fastapi import APIRouter, HTTPException
from ..deps import DB_PATH


router = APIRouter(tags=["peers"])


@router.get("/peers/{group_name}")
def peer_group(group_name: str, year: str = None):
    """All companies in a peer group with percentile rank for each of 10 metrics."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    members = conn.execute("SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name=?",
                            (group_name,)).fetchall()
    if not members:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Unknown peer group '{group_name}'")
    rows = conn.execute("SELECT * FROM peer_percentiles WHERE peer_group_name=?", (group_name,)).fetchall()
    conn.close()
    return {
        "peer_group": group_name,
        "members": [dict(m) for m in members],
        "percentiles": [dict(r) for r in rows],
    }
