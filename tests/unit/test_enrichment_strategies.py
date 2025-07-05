import pytest
from meshic_pipeline.enrichment import strategies


def test_quote_table_name_valid():
    assert strategies._quote_table_name("valid_table") == '"valid_table"'


def test_quote_table_name_invalid():
    with pytest.raises(ValueError):
        strategies._quote_table_name("bad;drop")
