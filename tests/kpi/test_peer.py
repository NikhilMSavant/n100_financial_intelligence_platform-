"""
Day 18 deliverable: unit tests for peer percentile computation.
Run with: python -m pytest tests/kpi/test_peer.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from peer import percent_rank


def test_01_percent_rank_five_companies_even_spacing():
    data = [("A", 10), ("B", 20), ("C", 30), ("D", 40), ("E", 50)]
    result = percent_rank(data)
    assert result["A"] == 0.0
    assert result["E"] == 1.0
    assert result["C"] == 0.5


def test_02_percent_rank_highest_value_gets_highest_rank():
    data = [("LOW", 1), ("MID", 50), ("HIGH", 99)]
    result = percent_rank(data)
    assert result["HIGH"] > result["MID"] > result["LOW"]


def test_03_percent_rank_none_value_excluded_but_others_still_ranked():
    data = [("A", 10), ("B", None), ("C", 30)]
    result = percent_rank(data)
    assert result["B"] is None
    assert result["A"] == 0.0
    assert result["C"] == 1.0


def test_04_percent_rank_single_company_gets_top_rank():
    result = percent_rank([("SOLO", 99)])
    assert result["SOLO"] == 1.0


def test_05_percent_rank_all_none_returns_all_none():
    data = [("A", None), ("B", None)]
    result = percent_rank(data)
    assert result["A"] is None
    assert result["B"] is None


def test_06_percent_rank_empty_list_returns_empty():
    result = percent_rank([])
    assert result == {}


def test_07_it_services_roe_ranking_matches_real_data():
    """Regression test for Day 21's exit criteria: within IT Services,
    the highest-ROE company must have the highest ROE percentile."""
    from peer import compute_peer_percentiles
    rows = compute_peer_percentiles()
    it_roe = [r for r in rows if r["peer_group_name"] == "IT Services" and r["metric"] == "roe"]
    it_roe_sorted_by_value = sorted(it_roe, key=lambda r: r["value"])
    it_roe_sorted_by_percentile = sorted(it_roe, key=lambda r: r["percentile_rank"])
    assert [r["company_id"] for r in it_roe_sorted_by_value] == [r["company_id"] for r in it_roe_sorted_by_percentile]


def test_08_de_inversion_lowest_de_gets_highest_percentile():
    from peer import compute_peer_percentiles
    rows = compute_peer_percentiles()
    de_rows = [r for r in rows if r["peer_group_name"] == "Private Banks" and r["metric"] == "debt_to_equity"]
    lowest_de_company = min(de_rows, key=lambda r: r["value"])
    assert lowest_de_company["percentile_rank"] == 1.0