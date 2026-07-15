from src.elt.normaliser import normalize_ticker


def test_ultratech():

    assert normalize_ticker(
        "ULTRATECH"
    ) == "ULTRACEMCO"


def test_vedanta():

    assert normalize_ticker(
        "VEDANTA"
    ) == "VEDL"


def test_unionbk():

    assert normalize_ticker(
        "UNIONBK"
    ) == "UNIONBANK"


def test_unknown():

    assert normalize_ticker(
        "TCS"
    ) == "TCS"