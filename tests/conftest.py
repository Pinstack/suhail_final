import pytest
import tempfile
import shutil
from unittest.mock import patch
from pathlib import Path

@pytest.fixture(scope="function")
def temp_cache_dir():
    """Provides a temporary directory for tile caching."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('src.meshic_pipeline.config.settings.cache_dir', Path(tmpdir)):
            yield Path(tmpdir)

@pytest.fixture(scope="function")
def mock_settings_tile_base_url():
    """Mocks the TILE_BASE_URL setting."""
    with patch('src.meshic_pipeline.config.settings.tile_base_url', "http://mock-tiles.com"):
        yield

