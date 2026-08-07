import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))
from normaliser import normalize_year, normalize_ticker, normalize_numeric, is_ttm


def test_normalize_year_mar_full():
    assert normalize_year("Mar 2014") == 2014


def test_normalize_year_mar_short():
    assert normalize_year("Mar-13") == 2013


def test_normalize_year_dec():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_ttm_is_none():
    assert normalize_year("TTM") is None


def test_normalize_year_none_input():
    assert normalize_year(None) is None


def test_normalize_year_garbage():
    assert normalize_year("not-a-year") is None


def test_normalize_year_sep():
    assert normalize_year("Sep 2024") == 2024


def test_is_ttm_true():
    assert is_ttm("TTM") is True


def test_is_ttm_false():
    assert is_ttm("Mar 2020") is False


def test_normalize_ticker_strips_and_upper():
    assert normalize_ticker("  tcs ") == "TCS"


def test_normalize_ticker_keeps_hyphen_amp():
    assert normalize_ticker("m&m") == "M&M"


def test_normalize_ticker_none():
    assert normalize_ticker(None) is None


def test_normalize_ticker_strips_punct():
    assert normalize_ticker("ABB!!") == "ABB"


def test_normalize_numeric_plain_float():
    assert normalize_numeric(12.5) == 12.5


def test_normalize_numeric_comma_string():
    assert normalize_numeric("1,234.5") == 1234.5


def test_normalize_numeric_dash_is_none():
    assert normalize_numeric("-") is None


def test_normalize_numeric_na_string_is_none():
    assert normalize_numeric("NA") is None


def test_normalize_numeric_none_is_none():
    assert normalize_numeric(None) is None


def test_normalize_numeric_garbage_is_none():
    assert normalize_numeric("abc") is None


def test_normalize_year_two_digit_boundary():
    assert normalize_year("Jun-99") == 2099  # documents the 2-digit rollover rule


def test_normalize_ticker_idempotent():
    assert normalize_ticker(normalize_ticker(" tcs ")) == "TCS"
