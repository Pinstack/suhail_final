import os
from src.meshic_pipeline.config import Settings, PIPELINE_CFG


def test_settings_loads_yaml_values():
    s = Settings()
    assert s.zoom == PIPELINE_CFG["zoom"]


def test_environment_variable_override(monkeypatch):
    monkeypatch.setenv("TILE_BASE_URL", "http://example.com")
    s = Settings()
    assert s.tile_base_url == "http://example.com"
