import pytest
import asyncio
from aioresponses import aioresponses
from src.meshic_pipeline.downloader.async_tile_downloader import AsyncTileDownloader
from src.meshic_pipeline.config import settings
from pathlib import Path

@pytest.fixture
async def downloader():
    async with AsyncTileDownloader() as dl:
        yield dl

@pytest.mark.asyncio
async def test_fetch_tile_success(downloader, temp_cache_dir, mock_settings_tile_base_url):
    z, x, y = 1, 2, 3
    tile_url = f"{settings.tile_base_url}/{z}/{x}/{y}.vector.pbf"
    expected_data = b"mock_tile_data"

    with aioresponses() as m:
        m.get(tile_url, status=200, body=expected_data)
        data = await downloader.fetch_tile(z, x, y)
        assert data == expected_data
        assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

@pytest.mark.asyncio
async def test_fetch_tile_404(downloader, temp_cache_dir, mock_settings_tile_base_url):
    z, x, y = 1, 2, 3
    tile_url = f"{settings.tile_base_url}/{z}/{x}/{y}.vector.pbf"

    with aioresponses() as m:
        m.get(tile_url, status=404)
        data = await downloader.fetch_tile(z, x, y)
        assert data is None
        assert not Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

@pytest.mark.asyncio
async def test_fetch_tile_retry(downloader, temp_cache_dir, mock_settings_tile_base_url):
    z, x, y = 1, 2, 3
    tile_url = f"{settings.tile_base_url}/{z}/{x}/{y}.vector.pbf"
    expected_data = b"mock_tile_data"

    with aioresponses() as m:
        # First request will fail with a 500 error
        m.get(tile_url, status=500)
        # The retry attempt will succeed with a 200 status
        m.get(tile_url, status=200, body=expected_data)

        data = await downloader.fetch_tile(z, x, y)
        assert data == expected_data
        assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

@pytest.mark.asyncio
async def test_download_many(downloader, temp_cache_dir, mock_settings_tile_base_url):
    tiles_to_download = [(1, 0, 0), (1, 0, 1), (1, 1, 0)]
    with aioresponses() as m:
        for z, x, y in tiles_to_download:
            tile_url = f"{settings.tile_base_url}/{z}/{x}/{y}.vector.pbf"
            m.get(tile_url, status=200, body=f"data_{z}_{x}_{y}".encode())

        downloaded_tiles = await downloader.download_many(tiles_to_download)

        assert len(downloaded_tiles) == len(tiles_to_download)
        for z, x, y in tiles_to_download:
            assert (z, x, y) in downloaded_tiles
            assert downloaded_tiles[(z, x, y)] == f"data_{z}_{x}_{y}".encode()
            assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()