import asyncio

import pytest

from meshic_pipeline.downloader.async_tile_downloader import AsyncTileDownloader

class FakeResponse:
    def __init__(self, status=200, data=b"data"):
        self.status = status
        self._data = data

    async def read(self):
        return self._data

    def raise_for_status(self):
        if self.status >= 400:
            import aiohttp
            raise aiohttp.ClientResponseError(None, (), status=self.status, message="error")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

class FakeSession:
    def __init__(self, response):
        self.response = response
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        return self.response

    async def close(self):
        pass

def test_fetch_tile_from_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    downloader = AsyncTileDownloader(base_url="http://example.com", cache_dir=cache_dir, session=FakeSession(FakeResponse()))
    cache_path = downloader.get_tile_cache_path(1, 2, 3)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_bytes(b"cached")

    async def run():
        async with downloader:
            data = await downloader.fetch_tile(1, 2, 3)
            assert data == b"cached"
            assert downloader.session.requested == []
    asyncio.run(run())

def test_fetch_tile_downloads_and_caches(tmp_path):
    response = FakeResponse(data=b"fresh")
    session = FakeSession(response)
    cache_dir = tmp_path / "cache"
    downloader = AsyncTileDownloader(base_url="http://example.com/tiles", cache_dir=cache_dir, session=session)

    async def run():
        async with downloader:
            data = await downloader.fetch_tile(1, 2, 3)
            assert data == b"fresh"
            expected_url = "http://example.com/tiles/1/2/3.vector.pbf"
            assert session.requested == [expected_url]
            assert downloader.get_tile_cache_path(1,2,3).read_bytes() == b"fresh"
    asyncio.run(run())
