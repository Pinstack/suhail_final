from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Sequence, Tuple

import aiohttp

logger = logging.getLogger(__name__)

TILE_URL_TEMPLATE = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"


class AsyncTileDownloader:
    def __init__(self, cache_dir: Path, max_concurrent: int = 32):
        self.cache_dir = cache_dir
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def fetch_tile(self, z: int, x: int, y: int) -> bytes | None:
        cache_path = self.cache_dir / str(z) / str(x) / f"{y}.pbf"
        if cache_path.exists():
            return cache_path.read_bytes()

        url = TILE_URL_TEMPLATE.format(z=z, x=x, y=y)
        async with self.semaphore:
            assert self.session is not None
            for attempt in range(3):
                try:
                    async with self.session.get(url) as resp:
                        if resp.status == 404:
                            logger.debug("Tile %s not found", url)
                            return None
                        resp.raise_for_status()
                        data = await resp.read()
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        cache_path.write_bytes(data)
                        return data
                except Exception as e:  # noqa: BLE001
                    logger.warning("Download failed (%s) attempt %d/3", e, attempt + 1)
                    await asyncio.sleep(2 ** attempt)
            logger.error("Failed to download tile %s after retries", url)
            return None

    async def download_many(self, tiles: Sequence[Tuple[int, int, int]]) -> dict[Tuple[int, int, int], bytes]:
        tasks = [self.fetch_tile(z, x, y) for z, x, y in tiles]
        results = await asyncio.gather(*tasks)
        return {tile: data for tile, data in zip(tiles, results) if data} 