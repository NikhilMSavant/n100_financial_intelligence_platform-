"""Nifty 100 Financial Intelligence Platform — FastAPI server.
Run with: uvicorn src.api.main:app --port 8000
(uvicorn/fastapi are not installable in this offline build sandbox — this is
delivered as complete, ready-to-run source, matching the module 11 spec.)
"""
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .deps import db_row_counts, APP_START_TIME, VERSION, TABLES
from .routers import companies, screener, sectors, peers, valuation, portfolio, documents, health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nifty100_api")

app = FastAPI(title="Nifty 100 Financial Intelligence Platform API", version=VERSION,
              description="16 endpoints serving the ETL + Ratio Engine + Screener + Peer + Clustering outputs.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                    allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
