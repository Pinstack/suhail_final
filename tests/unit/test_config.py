from meshic_pipeline.config import Settings, Environment


def test_environment_override():
    cfg = Settings(
        database_url="postgresql://user:pass@localhost/db", environment="testing"
    )
    assert cfg.environment == Environment.TESTING


def test_api_config_url_building():
    cfg = Settings(
        database_url="postgresql://user:pass@localhost/db",
        api_config={"base_url": "https://example.com"},
    )
    api = cfg.api_config
    assert api.transactions_url == "https://example.com/transactions"
    assert api.building_rules_url == "https://example.com/parcel/buildingRules"
    assert (
        api.price_metrics_url == "https://example.com/api/parcel/metrics/priceOfMeter"
    )


def test_get_tile_cache_path(tmp_path):
    cfg = Settings(
        database_url="postgresql://user:pass@localhost/db",
        cache_dir=tmp_path,
    )
    path = cfg.get_tile_cache_path(15, 1, 2)
    assert path == tmp_path / "15" / "1" / "2.pbf"
