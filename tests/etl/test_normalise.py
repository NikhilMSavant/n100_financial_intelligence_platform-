import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
from etl.normaliser import normalize_year, normalize_ticker


def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"

def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_mar_2023():
    assert normalize_year("Mar 2023") == "2023-03"

def test_year_march_dash_2023():
    assert normalize_year("March-2023") == "2023-03"

def test_year_plain_int():
    assert normalize_year("2023") == "2023-03"

def test_year_fy23():
    assert normalize_year("FY23") == "2023-03"

def test_year_fy2023():
    assert normalize_year("FY2023") == "2023-03"

def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"

def test_year_dec_2012():
    assert normalize_year("Dec 2012") == "2012-12"

def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"

def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"

def test_year_garbage():
    assert normalize_year("garbage") == "PARSE_ERROR"

def test_year_ttm():
    assert normalize_year("TTM") == "PARSE_ERROR"

def test_year_empty():
    assert normalize_year("") == "PARSE_ERROR"

def test_year_none():
    assert normalize_year(None) == "PARSE_ERROR"

def test_year_lowercase_month():
    assert normalize_year("mar-23") == "2023-03"

def test_year_sept_variant():
    assert normalize_year("Sept-23") == "2023-09"

def test_year_mar14():
    assert normalize_year("Mar 2014") == "2014-03"

def test_year_bad_month():
    assert normalize_year("Xyz-23") == "PARSE_ERROR"

def test_year_four_digit_only_2010():
    assert normalize_year("2010") == "2010-03"


def test_ticker_strip():
    assert normalize_ticker(" TCS ") == "TCS"

def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"

def test_ticker_hyphen_preserved():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

def test_ticker_ampersand_preserved():
    assert normalize_ticker("M&M") == "M&M"

def test_ticker_mixed_case():
    assert normalize_ticker("HdfcBank") == "HDFCBANK"

def test_ticker_none_raises():
    try:
        normalize_ticker(None)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_ticker_too_short_raises():
    try:
        normalize_ticker("A")
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_ticker_too_long_raises():
    try:
        normalize_ticker("A" * 20)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_ticker_numeric_ok():
    assert normalize_ticker("360ONE") == "360ONE"

def test_ticker_already_clean():
    assert normalize_ticker("WIPRO") == "WIPRO"

def test_ticker_trailing_newline():
    assert normalize_ticker("INFY\n") == "INFY"

def test_ticker_tab_whitespace():
    assert normalize_ticker("\tRELIANCE\t") == "RELIANCE"

def test_ticker_dot_preserved():
    # Some tickers may include a dot; ensure no crash / correct upper-casing
    assert normalize_ticker("abc.d") == "ABC.D"

def test_ticker_two_char_min():
    assert normalize_ticker("AB") == "AB"

def test_ticker_twelve_char_max():
    assert normalize_ticker("A" * 12) == "A" * 12
