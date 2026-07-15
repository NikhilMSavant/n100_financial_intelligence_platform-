from src.elt.normaliser import normalize_year


def test_mar_2024():

    assert normalize_year(
        "Mar 2024"
    ) == "Mar 2024"


def test_ttm():

    assert normalize_year(
        "TTM"
    ) == "TTM"


def test_strip_spaces():

    assert normalize_year(
        "  Mar 2022 "
    ) == "Mar 2022"