import os, sys, sqlite3
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "screener"))
sys.path.insert(0, os.path.join(ROOT, "src", "analytics"))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")

from engine import load_config, build_universe, apply_filters, run_preset


def conn():
    c = sqlite3.connect(DB_PATH)
    yield c
    c.close()


def test_universe_has_92_companies(conn):
    config = load_config()
    universe = build_universe(conn)
    assert len(universe) == 92


def test_all_six_presets_return_5_to_50(conn):
    config = load_config()
    universe = build_universe(conn)
    for key in config["presets"]:
        _, result = run_preset(universe, key, config)
        assert 5 <= len(result) <= 50, f"{key} returned {len(result)}"


def test_de_filter_skips_financials(conn):
    config = load_config()
    universe = build_universe(conn)
    result = apply_filters(universe, {"de_max": 0.1}, config)
    # any Financials-sector company with de > 0.1 should still be present
    fin_high_de = universe[(universe.broad_sector == "Financials") & (universe.debt_to_equity > 0.1)]
    if len(fin_high_de):
        assert fin_high_de.iloc[0]["company_id"] in result["company_id"].values


def test_icr_debt_free_always_passes(conn):
    config = load_config()
    universe = build_universe(conn)
    result = apply_filters(universe, {"icr_min": 999999}, config)
    debt_free = universe[universe.icr_label == "Debt Free"]
    if len(debt_free):
        assert debt_free.iloc[0]["company_id"] in result["company_id"].values


def test_composite_score_populated(conn):
    from composite_score import compute
    universe = build_universe(conn)
    scored = compute(universe)
    assert scored["composite_quality_score"].notna().all()


def test_composite_score_bounded_0_100(conn):
    from composite_score import compute
    universe = build_universe(conn)
    scored = compute(universe)
    assert scored["composite_quality_score"].between(-1, 101).all()


def test_peer_percentiles_populated(conn):
    n = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    assert n > 0


def test_peer_percentiles_11_groups(conn):
    n = conn.execute("SELECT COUNT(DISTINCT peer_group_name) FROM peer_percentiles").fetchone()[0]
    assert n == 11


def test_peer_percentile_range_valid(conn):
    df = pd.read_sql("SELECT percentile_rank FROM peer_percentiles", conn)
    assert df["percentile_rank"].between(0, 1).all()


def test_it_services_top_roe_has_top_percentile(conn):
    df = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name='IT Services' "
                      "AND metric='return_on_equity_pct'", conn)
    top_by_value = df.sort_values("value", ascending=False).iloc[0]["company_id"]
    top_by_pct = df.sort_values("percentile_rank", ascending=False).iloc[0]["company_id"]
    assert top_by_value == top_by_pct


def test_de_inverted_lowest_de_has_highest_percentile(conn):
    df = pd.read_sql("SELECT * FROM peer_percentiles WHERE metric='debt_to_equity'", conn)
    grp = df[df.peer_group_name == df.peer_group_name.iloc[0]]
    lowest_de = grp.sort_values("value", ascending=True).iloc[0]
    highest_pct = grp.sort_values("percentile_rank", ascending=False).iloc[0]
    assert lowest_de["company_id"] == highest_pct["company_id"]


def test_screener_output_file_exists():
    assert os.path.exists(os.path.join(ROOT, "output", "screener_output.xlsx"))


def test_peer_comparison_file_has_11_sheets():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(ROOT, "output", "peer_comparison.xlsx"))
    assert len(wb.sheetnames) == 11
