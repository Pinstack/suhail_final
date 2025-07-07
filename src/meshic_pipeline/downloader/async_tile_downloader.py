from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Sequence, Tuple

import aiohttp
from tqdm.asyncio import tqdm_asyncio

from ..config import settings

logger = logging.getLogger(__name__)


class AsyncTileDownloader:
    """Manages asynchronous download and caching of MVT tiles."""

    def __init__(
        self,
        base_url: str | None = None,
        cache_dir: str | Path | None = None,
        session: aiohttp.ClientSession | None = None,
    ):
        """Create a new downloader instance.

        Parameters
        ----------
        base_url:
            Optional custom base URL for tiles. If ``None`` the value from
            :data:`settings.tile_base_url` is used.
        cache_dir:
            Optional directory to store cached tiles. Defaults to
            :data:`settings.cache_dir`.
        session:
            Optional :class:`aiohttp.ClientSession` to use for requests. This
            allows tests to inject a fake session. If ``None`` a new session will
            be created when entering the async context manager.
        """

        self.cache_dir = Path(cache_dir) if cache_dir is not None else settings.cache_dir
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        self.session: aiohttp.ClientSession | None = session
        self._own_session = session is None
        self.base_url = (base_url or settings.tile_base_url).rstrip("/")

    async def __aenter__(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._own_session = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session and self._own_session:
            await self.session.close()

    def get_tile_cache_path(self, z: int, x: int, y: int) -> Path:
        """Return the cache path for the given tile coordinates."""
        tile_dir = self.cache_dir / str(z) / str(x)
        return tile_dir / f"{y}.pbf"

    async def fetch_tile(self, z: int, x: int, y: int) -> bytes | None:
        """Fetches a single tile, using the cache if available."""
        cache_path = self.get_tile_cache_path(z, x, y)
        if cache_path.exists():
            logger.debug("Tile %d/%d/%d found in cache.", z, x, y)
            return cache_path.read_bytes()

        url = f"{self.base_url}/{z}/{x}/{y}.vector.pbf"
        async with self.semaphore:
            assert self.session is not None
            # Stagger requests slightly to be a good neighbor
            await asyncio.sleep(settings.request_delay_seconds)
            
            for attempt in range(settings.retry_config.max_attempts):
                try:
                    logger.debug("Downloading tile: %s", url)
                    async with self.session.get(url) as resp:
                        if resp.status == 404:
                            logger.warning("Tile %s not found (404), skipping.", url)
                            return None
                        resp.raise_for_status()
                        
                        data = await resp.read()
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        cache_path.write_bytes(data)
                        logger.debug("Cached tile %s", cache_path)
                        return data
                except aiohttp.ClientError as e:
                    logger.warning(
                        "Download failed for %s (attempt %d/%d): %s",
                        url,
                        attempt + 1,
                        settings.retry_config.max_attempts,
                        e,
                    )
                    await asyncio.sleep(2**attempt) # Exponential backoff
            
            logger.error("Failed to download tile %s after multiple retries.", url)
            return None

    async def download_many(
        self, tiles: Sequence[Tuple[int, int, int]]
    ) -> dict[Tuple[int, int, int], bytes]:
        """Downloads a sequence of tiles concurrently with a progress bar."""
        tasks = [self.fetch_tile(z, x, y) for z, x, y in tiles]
        
        results = await tqdm_asyncio.gather(
            *tasks, desc=f"Downloading {len(tiles)} tiles", unit="tile"
        )
        
        # Filter out tiles that failed to download
        downloaded_tiles = {
            tile: data for tile, data in zip(tiles, results) if data is not None
        }
        
        failed_count = len(tiles) - len(downloaded_tiles)
        if failed_count > 0:
            logger.warning("%d tiles failed to download.", failed_count)
            
        return downloaded_tiles 
