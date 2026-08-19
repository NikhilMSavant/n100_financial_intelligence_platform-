"""API test suite using FastAPI's TestClient. NOTE: this sandbox has no
network access, so `fastapi`, `uvicorn`, and `httpx` could not be pip-installed
here — these tests are delivered as correct, ready-to-run source (matching the
Module 12 spec) but were not executed in this build. Run with:
    pip install fastapi uvicorn httpx
    pytest tests/api/
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_200():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_health_has_all_tables():
    r = client.get("/api/v1/health")
    counts = r.json()["db_row_counts"]
    assert len(counts) >= 10

def test_companies_count():
    r = client.get("/api/v1/companies")
    assert r.status_code == 200
    assert len(r.json()) == 92

def test_company_tcs_found():
    r = client.get("/api/v1/companies/TCS")
    assert r.status_code == 200
    assert r.json()["id"] == "TCS"

def test_invalid_ticker_404():
    r = client.get("/api/v1/companies/INVALIDTICKER")
    assert r.status_code == 404

def test_tcs_ratios_10plus_years():
    r = client.get("/api/v1/companies/TCS/ratios")
    assert r.status_code == 200
    assert len(r.json()) >= 10

def test_screener_min_roe_filter():
    r = client.get("/api/v1/screener", params={"min_roe": 15})
    assert r.status_code == 200
    assert all(row["return_on_equity_pct"] >= 15 for row in r.json())

def test_sectors_returns_list():
    r = client.get("/api/v1/sectors")
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_sector_it_companies_only():
    r = client.get("/api/v1/sectors/Information Technology/companies")
    assert r.status_code == 200
    assert len(r.json()) > 0

def test_unknown_sector_404():
    r = client.get("/api/v1/sectors/NotASector/companies")
    assert r.status_code == 404
