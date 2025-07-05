from meshic_pipeline.config import Settings, Environment, ApiConfig


def test_environment_override():
    cfg = Settings(
        database_url="postgresql://user:pass@localhost/db", environment="testing"
    )
    assert cfg.environment == Environment.TESTING


def test_api_config_url_building(monkeypatch):
    monkeypatch.setenv("SUHAIL_API_BASE_URL", "https://example.com")
    api = ApiConfig()
    assert api.transactions_url == "https://example.com/transactions"
    assert api.building_rules_url == "https://example.com/parcel/buildingRules"
    assert api.price_metrics_url == "https://example.com/api/parcel/metrics/priceOfMeter"


def test_get_tile_cache_path(tmp_path):
    cfg = Settings(
        database_url="postgresql://user:pass@localhost/db",
        cache_dir=tmp_path,
    )
    path = cfg.get_tile_cache_path(15, 1, 2)
    assert path == tmp_path / "15" / "1" / "2.pbf"
