import time
from fastapi import APIRouter
from ..deps import db_row_counts, APP_START_TIME, VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Server health check: DB row counts, uptime, and version."""
    return {
        "status": "ok",
        "db_row_counts": db_row_counts(),
        "uptime_seconds": round(time.time() - APP_START_TIME, 1),
        "version": VERSION,
    }
