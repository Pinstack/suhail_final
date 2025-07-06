import pytest
from meshic_pipeline.enrichment import strategies


def test_quote_table_name_valid():
    assert strategies._quote_table_name("valid_table") == '"valid_table"'


def test_quote_table_name_invalid():
    with pytest.raises(ValueError):
        strategies._quote_table_name("bad;drop")


def test_get_delta_query_contains_conditions():
    query = strategies._get_delta_query("temp_table")
    assert "COALESCE(p.transaction_price, 0) <= 0" in query
    assert "p.transaction_price > 0 AND f.transaction_price > 0" in query
