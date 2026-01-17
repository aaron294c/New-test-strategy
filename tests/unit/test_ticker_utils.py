import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from ticker_utils import resolve_yahoo_symbol  # noqa: E402


def test_resolve_yahoo_symbol_maps_lse_aliases():
    assert resolve_yahoo_symbol("CNX1") == "CNX1.L"
    assert resolve_yahoo_symbol("cnx1") == "CNX1.L"
    assert resolve_yahoo_symbol("CNX1.L") == "CNX1.L"


def test_resolve_yahoo_symbol_supports_exchange_prefix():
    assert resolve_yahoo_symbol("LON:CNX1") == "CNX1.L"
    assert resolve_yahoo_symbol("LSE:CNX1") == "CNX1.L"


def test_resolve_yahoo_symbol_maps_share_class_dot_to_dash():
    assert resolve_yahoo_symbol("brk.b") == "BRK-B"
    assert resolve_yahoo_symbol("BF.B") == "BF-B"
