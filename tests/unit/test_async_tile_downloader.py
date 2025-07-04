import pytest
import asyncio
from unittest.mock import AsyncMock
import aiohttp


class MockResponse:
    def __init__(self, status: int, body: bytes = b""):
        self.status = status
        self._body = body

    async def read(self) -> bytes:
        return self._body

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientError(f"{self.status}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
from src.meshic_pipeline.downloader.async_tile_downloader import AsyncTileDownloader
from src.meshic_pipeline.config import settings
from pathlib import Path

def test_fetch_tile_success(temp_cache_dir, mock_settings_tile_base_url):
    async def run():
        z, x, y = 1, 2, 3
        expected_data = b"mock_tile_data"

        async with AsyncTileDownloader() as downloader:
            def mock_get(url, *args, **kwargs):
                return MockResponse(200, expected_data)

            downloader.session.get = mock_get
            data = await downloader.fetch_tile(z, x, y)
            assert data == expected_data
            assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

    asyncio.run(run())

def test_fetch_tile_404(temp_cache_dir, mock_settings_tile_base_url):
    async def run():
        z, x, y = 1, 2, 3

        async with AsyncTileDownloader() as downloader:
            def mock_get(url, *args, **kwargs):
                return MockResponse(404)

            downloader.session.get = mock_get
            data = await downloader.fetch_tile(z, x, y)
            assert data is None
            assert not Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

    asyncio.run(run())

def test_fetch_tile_retry(temp_cache_dir, mock_settings_tile_base_url):
    async def run():
        z, x, y = 1, 2, 3
        expected_data = b"mock_tile_data"

        responses = iter([
            MockResponse(500),
            MockResponse(200, expected_data),
        ])

        async with AsyncTileDownloader() as downloader:
            def mock_get(url, *args, **kwargs):
                return next(responses)

            downloader.session.get = mock_get

            data = await downloader.fetch_tile(z, x, y)
            assert data == expected_data
            assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

    asyncio.run(run())

def test_download_many(temp_cache_dir, mock_settings_tile_base_url):
    async def run():
        tiles_to_download = [(1, 0, 0), (1, 0, 1), (1, 1, 0)]
        responses = {
            (z, x, y): MockResponse(200, f"data_{z}_{x}_{y}".encode())
            for z, x, y in tiles_to_download
        }

        async with AsyncTileDownloader() as downloader:
            def mock_get(url, *args, **kwargs):
                parts = url.rstrip(".vector.pbf").split("/")
                z, x, y = map(int, parts[-3:])
                return responses[(z, x, y)]

            downloader.session.get = mock_get

            downloaded_tiles = await downloader.download_many(tiles_to_download)

            assert len(downloaded_tiles) == len(tiles_to_download)
            for z, x, y in tiles_to_download:
                assert (z, x, y) in downloaded_tiles
                assert downloaded_tiles[(z, x, y)] == f"data_{z}_{x}_{y}".encode()
                assert Path(temp_cache_dir / settings.get_tile_cache_path(z, x, y)).exists()

    asyncio.run(run())
