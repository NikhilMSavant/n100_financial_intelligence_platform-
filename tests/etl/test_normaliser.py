"""
Day 2 deliverable: 35+ unit tests for normaliser.py
20 for normalize_year(), 15 for normalize_ticker(), matching the sprint's test-count target.
Run with: python -m pytest tests/etl/test_normaliser.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))

import pytest
from normaliser import normalize_year, normalize_ticker, YearNormalizationError


# ---------- normalize_year: 20 tests ----------

def test_year_01_mon_yyyy_dec():
    assert normalize_year("Dec 2012") == "2012-12"

def test_year_02_mon_yyyy_mar():
    assert normalize_year("Mar 2014") == "2014-03"

def test_year_03_mon_yyyy_jun():
    assert normalize_year("Jun 2015") == "2015-06"

def test_year_04_mon_yyyy_sep():
    assert normalize_year("Sep 2024") == "2024-09"

def test_year_05_hyphenated_2digit():
    assert normalize_year("Mar-13") == "2013-03"

def test_year_06_hyphenated_2digit_late():
    assert normalize_year("Mar-24") == "2024-03"

def test_year_07_ttm_sentinel():
    assert normalize_year("TTM") == "TTM"

def test_year_08_ttm_case_insensitive():
    assert normalize_year("ttm") == "TTM"

def test_year_09_trailing_junk_number():
    assert normalize_year("Mar 2023 15") == "2023-03"

def test_year_10_trailing_junk_9m():
    assert normalize_year("Mar 2016 9m") == "2016-03"

def test_year_11_bare_year_string():
    assert normalize_year("2013") == "2013-03"

def test_year_12_bare_year_int():
    assert normalize_year(2024) == "2024-03"

def test_year_13_bare_year_float_corruption():
    assert normalize_year(2024.5) == "2024-03"

def test_year_14_none_returns_none():
    assert normalize_year(None) is None

def test_year_15_empty_string_returns_none():
    assert normalize_year("") is None

def test_year_16_garbage_returns_none():
    assert normalize_year("not a year") is None

def test_year_17_out_of_range_year():
    assert normalize_year("1500") is None

def test_year_18_strict_raises_on_garbage():
    with pytest.raises(YearNormalizationError):
        normalize_year("garbage", strict=True)

def test_year_19_custom_default_month():
    assert normalize_year("2020", default_month=12) == "2020-12"

def test_year_20_whitespace_padded():
    assert normalize_year("  Dec 2012  ") == "2012-12"


# ---------- normalize_ticker: 15 tests ----------

def test_ticker_01_already_clean():
    assert normalize_ticker("TCS") == "TCS"

def test_ticker_02_lowercase():
    assert normalize_ticker("hdfcbank") == "HDFCBANK"

def test_ticker_03_leading_trailing_space():
    assert normalize_ticker("  abb  ") == "ABB"

def test_ticker_04_internal_space_collapsed():
    assert normalize_ticker("ADANI ENSOL") == "ADANIENSOL"

def test_ticker_05_mixed_case():
    assert normalize_ticker("AdaniGreen") == "ADANIGREEN"

def test_ticker_06_none_returns_none():
    assert normalize_ticker(None) is None

def test_ticker_07_empty_string_returns_none():
    assert normalize_ticker("") is None

def test_ticker_08_whitespace_only_returns_none():
    assert normalize_ticker("   ") is None

def test_ticker_09_strict_raises_on_empty():
    with pytest.raises(ValueError):
        normalize_ticker("", strict=True)

def test_ticker_10_numeric_like_ticker():
    assert normalize_ticker("360one") == "360ONE"

def test_ticker_11_idempotent():
    once = normalize_ticker(" tcs ")
    twice = normalize_ticker(once)
    assert once == twice == "TCS"

def test_ticker_12_tabs_and_newlines():
    assert normalize_ticker("\tTCS\n") == "TCS"

def test_ticker_13_single_char_ok():
    assert normalize_ticker("a") == "A"

def test_ticker_14_preserves_digits():
    assert normalize_ticker("m&m") == "M&M"

def test_ticker_15_preserves_hyphen():
    assert normalize_ticker("l&t-fh") == "L&T-FH"
