from meshic_pipeline.config import Settings, Environment


def test_environment_override():
    cfg = Settings(database_url="postgresql://user:pass@localhost/db", environment="testing")
    assert cfg.environment == Environment.TESTING
