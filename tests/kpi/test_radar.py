"""
Day 19 deliverable: unit tests for radar chart data preparation.
Note: we test the DATA PREPARATION logic (build_radar_dataframe, axis
scaling), not the actual image rendering, since verifying pixel output
isn't practical in a unit test - the visual charts were manually
reviewed during development instead.
Run with: python -m pytest tests/kpi/test_radar.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from radar import build_radar_dataframe, RADAR_AXES


def test_01_all_92_companies_present():
    df = build_radar_dataframe()
    assert len(df) == 92


def test_02_all_8_axis_columns_exist():
    df = build_radar_dataframe()
    for axis in RADAR_AXES:
        assert f"axis_{axis}" in df.columns


def test_03_axis_values_within_0_to_100_or_null():
    df = build_radar_dataframe()
    for axis in RADAR_AXES:
        col = df[f"axis_{axis}"]
        valid = col.dropna()
        assert (valid >= 0).all() and (valid <= 100).all(), f"{axis} has values outside 0-100"


def test_04_known_bad_company_roe_axis_is_null():
    df = build_radar_dataframe()
    bel_row = df[df["company_id"] == "BEL"].iloc[0]
    assert bel_row["axis_ROE"] is None or bel_row["axis_ROE"] != bel_row["axis_ROE"]  # None or NaN


def test_05_radar_chart_files_exist_for_all_companies():
    import os
    files = set(os.listdir("reports/radar_charts"))
    df = build_radar_dataframe()
    for cid in df["company_id"]:
        safe_cid = cid.replace("&", "AND").replace("/", "-")
        assert f"{safe_cid}_radar.png" in files, f"missing chart for {cid}"